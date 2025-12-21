"""Cloudflare bypass utilities.

Provides functions and constants for bypassing Cloudflare protection
using cloudscraper with multiple fallback strategies.
"""
from __future__ import annotations

import logging
import time
from typing import Any

import cloudscraper
import requests

logger = logging.getLogger(__name__)

# Cloudflare-related status codes that might be worth retrying
CLOUDFLARE_RETRY_CODES = {403, 429, 503, 520, 521, 522, 523, 524}

# Browser profiles to try in order of preference
BROWSER_PROFILES = [
    {"browser": "chrome", "platform": "linux", "desktop": True},
    {"browser": "chrome", "platform": "windows", "desktop": True},
    {"browser": "chrome", "platform": "darwin", "desktop": True},
    {"browser": "firefox", "platform": "linux", "desktop": True},
    {"browser": "firefox", "platform": "windows", "desktop": True},
]

# Common headers that make requests look more like a real browser
BROWSER_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}


def create_cloudflare_session(
    delay: int = 3,
    browser: str = "chrome",
    platform: str = "linux",
) -> requests.Session:
    """Create a cloudscraper session configured for Cloudflare bypass.

    Args:
        delay: Delay in seconds for challenge solving (default: 3)
        browser: Browser to emulate (chrome, firefox)
        platform: Platform to emulate (linux, windows, darwin)

    Returns:
        A cloudscraper session ready for Cloudflare-protected sites
    """
    session = cloudscraper.create_scraper(
        browser={"browser": browser, "platform": platform, "desktop": True},
        delay=delay,
    )
    session.headers.update(BROWSER_HEADERS)
    return session


def create_cloudflare_session_with_fallback(
    base_url: str,
    timeout_seconds: float = 15.0,
) -> requests.Session:
    """Create a session with Cloudflare bypass, trying multiple strategies.

    Attempts different browser profiles and configurations until one works.

    Args:
        base_url: The base URL to test against
        timeout_seconds: Timeout for test requests

    Returns:
        A cloudscraper session configured to bypass Cloudflare
    """
    base_url = base_url.rstrip("/")

    for profile in BROWSER_PROFILES:
        try:
            session = cloudscraper.create_scraper(
                browser=profile,
                delay=3,  # Add delay for challenge solving
            )
            session.headers.update(BROWSER_HEADERS)

            # Test if this profile works
            test_resp = session.get(
                f"{base_url}/",
                timeout=timeout_seconds,
                allow_redirects=True,
            )
            if test_resp.status_code == 200:
                logger.info(f"Cloudflare bypass successful with profile: {profile}")
                return session
            elif test_resp.status_code == 403:
                logger.warning(f"Profile {profile} got 403, trying next...")
                continue
        except Exception as e:
            logger.warning(f"Profile {profile} failed: {e}, trying next...")
            continue

    # Fallback: return last session even if it didn't fully work
    logger.warning("All browser profiles failed, using last session as fallback")
    session = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "linux", "desktop": True},
        delay=5,
    )
    session.headers.update(BROWSER_HEADERS)
    return session


def warm_up_session(
    session: requests.Session,
    base_url: str,
    timeout_seconds: float = 15.0,
    with_delay: bool = True,
) -> bool:
    """Warm up a session to obtain Cloudflare cookies.

    Args:
        session: The session to warm up
        base_url: Base URL of the site
        timeout_seconds: Request timeout
        with_delay: Add delays between requests

    Returns:
        True if at least one warm-up request succeeded
    """
    base_url = base_url.rstrip("/")
    warmup_urls = [
        f"{base_url}/",
        f"{base_url}/about",
    ]

    success = False
    for i, url in enumerate(warmup_urls):
        try:
            resp = session.get(
                url,
                timeout=timeout_seconds,
                allow_redirects=True,
            )
            if resp.status_code == 200:
                success = True
                logger.debug(f"Warm-up successful: {url}")
            else:
                logger.warning(f"Warm-up got status {resp.status_code}: {url}")

            # Add delay between requests
            if with_delay and i < len(warmup_urls) - 1:
                time.sleep(0.5)
        except requests.RequestException as e:
            logger.warning(f"Warm-up failed for {url}: {e}")

    return success


def extended_warm_up(
    session: requests.Session,
    base_url: str,
    timeout_seconds: float = 15.0,
) -> None:
    """Extended warm-up with delays and multiple page visits.

    More aggressive than basic warm-up to help with Cloudflare challenges.

    Args:
        session: The session to warm up
        base_url: Base URL of the site
        timeout_seconds: Request timeout
    """
    base_url = base_url.rstrip("/")
    warmup_urls = [
        f"{base_url}/",
        f"{base_url}/about",
        f"{base_url}/categories",
        f"{base_url}/top",
    ]

    for i, url in enumerate(warmup_urls):
        try:
            resp = session.get(
                url,
                timeout=timeout_seconds,
                allow_redirects=True,
            )
            if resp.status_code == 200:
                logger.debug(f"Warm-up successful for {url}")
            else:
                logger.warning(f"Warm-up got status {resp.status_code} for {url}")

            # Add delay between requests to avoid rate limiting
            if i < len(warmup_urls) - 1:
                time.sleep(0.5)
        except requests.RequestException as e:
            logger.warning(f"Warm-up failed for {url}: {e}")


def is_cloudflare_challenge(response: requests.Response) -> bool:
    """Check if a response is a Cloudflare challenge page.

    Args:
        response: The response to check

    Returns:
        True if this looks like a Cloudflare challenge
    """
    if response.status_code != 200:
        return False

    content_type = response.headers.get("Content-Type", "")
    if "text/html" not in content_type:
        return False

    content_lower = response.text[:1000].lower()
    return "cloudflare" in content_lower or "challenge" in content_lower


def is_cloudflare_error(status_code: int) -> bool:
    """Check if a status code is a Cloudflare-related error.

    Args:
        status_code: HTTP status code

    Returns:
        True if this is a Cloudflare-related error code
    """
    return status_code in CLOUDFLARE_RETRY_CODES

