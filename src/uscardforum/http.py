"""HTTP utilities for the USCardForum client.

Provides rate-limited, retry-enabled HTTP request helpers for interacting
with Discourse API endpoints.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

import backoff
import requests
from ratelimit import limits, sleep_and_retry


# Only retry on transient errors, not client errors (4xx)
RETRYABLE_EXCEPTIONS = (
    requests.exceptions.ConnectionError,
    requests.exceptions.Timeout,
    requests.exceptions.ChunkedEncodingError,
)


def _is_retryable_status(exc: Exception) -> bool:
    """Check if an HTTPError should be retried (5xx server errors only)."""
    if isinstance(exc, requests.exceptions.HTTPError):
        if exc.response is not None:
            # Retry on 5xx server errors and 429 (rate limited)
            return exc.response.status_code >= 500 or exc.response.status_code == 429
    return True  # Retry other exceptions


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
@limits(calls=4, period=1)
@backoff.on_exception(
    backoff.expo,
    (requests.exceptions.HTTPError, *RETRYABLE_EXCEPTIONS),
    max_tries=3,
    giveup=lambda e: not _is_retryable_status(e),
    max_time=30,
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
    resp = session.request(
        method.upper(),
        url,
        params=params,
        json=json,
        data=data,
        headers=headers,
        timeout=timeout_seconds,
    )
    resp.raise_for_status()
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
        return resp.json()
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

