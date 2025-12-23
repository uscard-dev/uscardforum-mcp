"""HTTP utilities for the USCardForum client.

Provides rate-limited, retry-enabled HTTP request helpers for interacting
with Discourse API endpoints.
"""
from __future__ import annotations

import json
import logging
from collections.abc import Mapping, Sequence
from typing import Any

import backoff
import requests
from ratelimit import limits, sleep_and_retry

from uscardforum.utils.cloudflare import CLOUDFLARE_RETRY_CODES, is_cloudflare_challenge

logger = logging.getLogger(__name__)

# Only retry on transient errors, not client errors (4xx)
RETRYABLE_EXCEPTIONS = (
    requests.exceptions.ConnectionError,
    requests.exceptions.Timeout,
    requests.exceptions.ChunkedEncodingError,
)


class DiscourseHTTPError(requests.exceptions.HTTPError):
    """HTTPError with enhanced error message from Discourse API response."""

    def __init__(
        self,
        original: requests.exceptions.HTTPError,
        detail: str | None = None,
    ) -> None:
        self.original = original
        self.detail = detail
        self.response = original.response
        super().__init__(str(self), response=original.response)

    def __str__(self) -> str:
        status = self.response.status_code if self.response is not None else "?"
        if self.detail:
            return f"HTTP Error {status}: {self.detail}"
        return f"HTTP Error {status}"


def _extract_discourse_error(resp: requests.Response) -> str | None:
    """Extract error message from Discourse API response.

    Discourse returns errors in various formats:
    - {"errors": ["error message 1", "error message 2"]}
    - {"error": "single error message"}
    - {"failed": "FAILED", "message": "error details"}

    Args:
        resp: Response object to extract error from

    Returns:
        Error message string or None if not extractable
    """
    if resp is None:
        return None

    try:
        data = resp.json()
        # Check for "errors" array (most common)
        if isinstance(data.get("errors"), list) and data["errors"]:
            return "; ".join(str(e) for e in data["errors"])
        # Check for single "error" field
        if data.get("error"):
            return str(data["error"])
        # Check for "message" field (used in some error responses)
        if data.get("message"):
            return str(data["message"])
        # Check for "error_type" with additional info
        if data.get("error_type"):
            error_type = data["error_type"]
            extras = data.get("extras", {})
            if extras:
                return f"{error_type}: {json.dumps(extras)}"
            return str(error_type)
    except (ValueError, TypeError, KeyError):
        # Not JSON or unexpected format - try to get text snippet
        pass

    # Fall back to text snippet if available
    if resp.text:
        snippet = resp.text[:200].strip()
        if snippet:
            return snippet

    return None


def _raise_with_detail(exc: requests.exceptions.HTTPError) -> None:
    """Re-raise HTTPError with Discourse error details if available.

    Args:
        exc: Original HTTPError

    Raises:
        DiscourseHTTPError: Enhanced error with details from response
    """
    detail = _extract_discourse_error(exc.response) if exc.response is not None else None
    raise DiscourseHTTPError(exc, detail=detail) from exc


def _is_retryable_status(exc: Exception) -> bool:
    """Check if an HTTPError should be retried.

    Retries on:
    - 5xx server errors
    - 429 rate limited
    - 403 Forbidden (might be Cloudflare challenge)
    - Cloudflare-specific error codes (520-524)
    """
    if isinstance(exc, (requests.exceptions.HTTPError, DiscourseHTTPError)):
        response = getattr(exc, "response", None)
        if response is not None:
            status = response.status_code
            # Retry on 5xx, 429, 403 (Cloudflare), and Cloudflare-specific codes
            return status >= 500 or status in CLOUDFLARE_RETRY_CODES
    return True  # Retry other exceptions


def _on_backoff(details: dict[str, Any]) -> None:
    """Log when backing off due to an error."""
    exc = details.get("exception")
    wait = details.get("wait", 0)
    tries = details.get("tries", 0)
    if exc and isinstance(exc, (requests.exceptions.HTTPError, DiscourseHTTPError)):
        response = getattr(exc, "response", None)
        if response is not None:
            logger.warning(
                f"Request failed with status {response.status_code}, "
                f"retry {tries}, waiting {wait:.1f}s"
            )
            return
    logger.warning(f"Request failed, retry {tries}, waiting {wait:.1f}s: {exc}")


def full_url(base_url: str, path_or_url: str) -> str:
    """Return absolute URL for given path or already-absolute URL.

    Args:
        base_url: The base URL of the forum (e.g., https://www.uscardforum.com)
        path_or_url: Either a relative path or full URL

    Returns:
        Fully qualified URL
    """
    if path_or_url.startswith(("http://", "https://")):
        return path_or_url

    return f"{base_url.rstrip('/')}/{path_or_url.lstrip('/')}"


@sleep_and_retry
@limits(calls=3, period=1)  # Slightly slower rate to avoid Cloudflare triggers
@backoff.on_exception(
    backoff.expo,
    (requests.exceptions.HTTPError, DiscourseHTTPError, *RETRYABLE_EXCEPTIONS),
    max_tries=5,  # More retries for Cloudflare
    giveup=lambda e: not _is_retryable_status(e),
    max_time=60,  # Longer max time for challenge solving
    on_backoff=_on_backoff,  # type: ignore[arg-type]
    factor=2,  # Start with 2 second delay, then 4, 8, etc.
)
def request(
    session: requests.Session,
    method: str,
    base_url: str,
    path_or_url: str,
    *,
    timeout_seconds: float,
    params: Mapping[str, Any] | Sequence[tuple[str, Any]] | None = None,
    json: dict[str, Any] | None = None,
    data: dict[str, Any] | Sequence[tuple[str, Any]] | None = None,
    headers: Mapping[str, str] | None = None,
) -> requests.Response:
    """Send an HTTP request with rate limiting and automatic retries.

    Args:
        session: requests Session to use
        method: HTTP method (GET, POST, etc.)
        base_url: Base URL of the API
        path_or_url: Endpoint path or full URL
        timeout_seconds: Request timeout
        params: Query parameters
        json: JSON body data
        data: Form data
        headers: HTTP headers

    Returns:
        Response object

    Raises:
        HTTPError: If request fails after retries
    """
    url = full_url(base_url, path_or_url)

    # Add delay before request if we've had Cloudflare issues
    # (cloudscraper may need time to solve challenges)

    resp = session.request(
        method.upper(),
        url,
        params=params,
        json=json,
        data=data,  # type: ignore[arg-type]
        headers=headers,
        timeout=timeout_seconds,
    )

    # Check for Cloudflare challenge page in HTML response
    if is_cloudflare_challenge(resp):
        logger.warning("Detected Cloudflare challenge page, may need retry")
        # Let cloudscraper handle it on retry
        resp.status_code = 503  # Force retry
        resp.raise_for_status()

    try:
        resp.raise_for_status()
    except requests.exceptions.HTTPError as exc:
        _raise_with_detail(exc)

    return resp


def parse_json_or_raise(resp: requests.Response) -> dict[str, Any]:
    """Parse JSON response or raise informative error.

    Args:
        resp: Response object to parse

    Returns:
        Parsed JSON as dictionary

    Raises:
        RuntimeError: If response is not valid JSON
    """
    try:
        result: dict[str, Any] = resp.json()
        return result
    except ValueError as exc:
        ct = resp.headers.get("Content-Type", "")
        snippet = resp.text[:200] if resp.text else "<empty body>"
        raise RuntimeError(
            f"Expected JSON but got Content-Type '{ct}'. Body starts with: {snippet}"
        ) from exc


def request_json(
    session: requests.Session,
    method: str,
    base_url: str,
    path_or_url: str,
    *,
    timeout_seconds: float,
    params: Mapping[str, Any] | Sequence[tuple[str, Any]] | None = None,
    json: dict[str, Any] | None = None,
    data: dict[str, Any] | Sequence[tuple[str, Any]] | None = None,
    headers: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Send request and parse JSON response.

    Combines request() and parse_json_or_raise() for convenience.

    Args:
        session: requests Session to use
        method: HTTP method
        base_url: Base URL of the API
        path_or_url: Endpoint path or full URL
        timeout_seconds: Request timeout
        params: Query parameters
        json: JSON body data
        data: Form data
        headers: HTTP headers

    Returns:
        Parsed JSON response as dictionary
    """
    resp = request(
        session,
        method,
        base_url,
        path_or_url,
        timeout_seconds=timeout_seconds,
        params=params,
        json=json,
        data=data,
        headers=headers,
    )
    return parse_json_or_raise(resp)

