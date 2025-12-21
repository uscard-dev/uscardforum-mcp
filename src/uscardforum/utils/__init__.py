"""Utility modules for USCardForum client.

This package contains:
- cloudflare: Cloudflare bypass utilities
- http: HTTP request helpers with rate limiting and retries
"""

from uscardforum.utils.cloudflare import (
    BROWSER_HEADERS,
    BROWSER_PROFILES,
    CLOUDFLARE_RETRY_CODES,
    create_cloudflare_session,
    create_cloudflare_session_with_fallback,
    extended_warm_up,
    is_cloudflare_challenge,
    is_cloudflare_error,
    warm_up_session,
)
from uscardforum.utils.http import (
    full_url,
    parse_json_or_raise,
    request,
    request_json,
)

__all__ = [
    # Cloudflare
    "BROWSER_HEADERS",
    "BROWSER_PROFILES",
    "CLOUDFLARE_RETRY_CODES",
    "create_cloudflare_session",
    "create_cloudflare_session_with_fallback",
    "extended_warm_up",
    "is_cloudflare_challenge",
    "is_cloudflare_error",
    "warm_up_session",
    # HTTP
    "full_url",
    "parse_json_or_raise",
    "request",
    "request_json",
]

