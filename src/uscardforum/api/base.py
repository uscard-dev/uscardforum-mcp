"""Base API client with HTTP methods."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import requests

from uscardforum.utils.http import request_json


class BaseAPI:
    """Base class for API modules with HTTP helper methods.

    Provides the foundation for all API modules with:
    - HTTP request methods with rate limiting
    - Session management
    - JSON parsing
    """

    def __init__(
        self,
        session: requests.Session,
        base_url: str,
        timeout_seconds: float = 15.0,
    ) -> None:
        """Initialize base API.

        Args:
            session: Requests session (should be cloudscraper for Cloudflare)
            base_url: Forum base URL
            timeout_seconds: Default request timeout
        """
        self._session = session
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | Sequence[tuple[str, Any]] | None = None,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | Sequence[tuple[str, Any]] | None = None,
        headers: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """Make a JSON API request.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API endpoint path
            params: Query parameters
            json: JSON body
            data: Form data
            headers: HTTP headers
            timeout: Request timeout (uses default if not specified)

        Returns:
            Parsed JSON response
        """
        return request_json(
            self._session,
            method,
            self._base_url,
            path,
            timeout_seconds=timeout or self._timeout_seconds,
            params=params,
            json=json,
            data=data,
            headers=headers,
        )

    def _get(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | Sequence[tuple[str, Any]] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        """Make a GET request."""
        default_headers = {"Accept": "application/json"}
        if headers:
            default_headers.update(headers)
        return self._request_json("get", path, params=params, headers=default_headers)

    def _post(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | Sequence[tuple[str, Any]] | None = None,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | Sequence[tuple[str, Any]] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        """Make a POST request."""
        default_headers = {"Accept": "application/json"}
        if headers:
            default_headers.update(headers)
        return self._request_json(
            "post", path, params=params, json=json, data=data, headers=default_headers
        )

