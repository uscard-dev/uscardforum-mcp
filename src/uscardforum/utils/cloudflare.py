"""Cloudflare bypass utilities.

Provides functions and constants for bypassing Cloudflare protection
using multiple strategies in order:
1. cloudscraper (multiple browser profiles)
2. curl_cffi (real browser TLS fingerprints)
3. Playwright with stealth (real browser fallback)
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

# Browser profiles for cloudscraper
BROWSER_PROFILES = [
    {"browser": "chrome", "platform": "linux", "desktop": True},
    {"browser": "chrome", "platform": "windows", "desktop": True},
    {"browser": "chrome", "platform": "darwin", "desktop": True},
    {"browser": "firefox", "platform": "linux", "desktop": True},
    {"browser": "firefox", "platform": "windows", "desktop": True},
]

# curl_cffi browser impersonation profiles (TLS fingerprints)
CURL_CFFI_IMPERSONATES = [
    "chrome120",
    "chrome119",
    "chrome110",
    "chrome107",
    "chrome104",
    "edge101",
    "safari15_5",
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


class CurlCffiSessionWrapper:
    """Wrapper to make curl_cffi.Session behave like requests.Session.
    
    This allows curl_cffi to be used as a drop-in replacement.
    """
    
    def __init__(self, impersonate: str = "chrome120"):
        try:
            from curl_cffi.requests import Session
            self._session = Session(impersonate=impersonate)
            self._impersonate = impersonate
            self.headers = dict(BROWSER_HEADERS)
            self.cookies = self._session.cookies
        except ImportError:
            raise ImportError("curl_cffi not available")
    
    def get(self, url: str, **kwargs) -> requests.Response:
        """Make GET request and convert response to requests-compatible format."""
        kwargs.setdefault("headers", self.headers)
        kwargs.setdefault("timeout", 15)
        resp = self._session.get(url, **kwargs)
        return self._convert_response(resp)
    
    def post(self, url: str, **kwargs) -> requests.Response:
        """Make POST request and convert response to requests-compatible format."""
        kwargs.setdefault("headers", self.headers)
        kwargs.setdefault("timeout", 15)
        resp = self._session.post(url, **kwargs)
        return self._convert_response(resp)
    
    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make any HTTP request."""
        kwargs.setdefault("headers", self.headers)
        kwargs.setdefault("timeout", 15)
        resp = self._session.request(method, url, **kwargs)
        return self._convert_response(resp)
    
    def _convert_response(self, curl_resp: Any) -> requests.Response:
        """Convert curl_cffi response to requests.Response-like object."""
        # curl_cffi responses are already compatible enough
        return curl_resp


def _create_session_with_curl_cffi(
    base_url: str,
    timeout_seconds: float = 15.0,
) -> requests.Session | None:
    """Create a session using curl_cffi with browser TLS fingerprints.
    
    curl_cffi impersonates real browser TLS fingerprints, which is very
    effective against Cloudflare's TLS fingerprinting.
    
    Args:
        base_url: The base URL to test against
        timeout_seconds: Timeout for test requests
        
    Returns:
        A curl_cffi session wrapper, or None if failed
    """
    try:
        from curl_cffi.requests import Session
    except ImportError:
        logger.warning("curl_cffi not available, skipping TLS fingerprint bypass")
        return None
    
    base_url = base_url.rstrip("/")
    
    for impersonate in CURL_CFFI_IMPERSONATES:
        try:
            session = Session(impersonate=impersonate)
            
            # Test if this impersonation works
            test_resp = session.get(
                f"{base_url}/",
                timeout=timeout_seconds,
                allow_redirects=True,
            )
            
            if test_resp.status_code == 200:
                logger.info(f"Cloudflare bypass successful with curl_cffi impersonate={impersonate}")
                # Return wrapped session
                wrapper = CurlCffiSessionWrapper(impersonate=impersonate)
                return wrapper  # type: ignore
            elif test_resp.status_code == 403:
                logger.warning(f"curl_cffi {impersonate} got 403, trying next...")
                continue
        except Exception as e:
            logger.warning(f"curl_cffi {impersonate} failed: {e}, trying next...")
            continue
    
    logger.warning("All curl_cffi impersonations failed")
    return None


def _create_session_with_playwright(
    base_url: str,
    timeout_seconds: float = 30.0,
    headless: bool = True,
) -> requests.Session | None:
    """Create a requests session using cookies obtained from Playwright with stealth.

    Uses a real browser to solve Cloudflare challenges and transfers cookies
    to a requests session.

    Args:
        base_url: The base URL to navigate to
        timeout_seconds: Timeout for page load
        headless: Run browser in headless mode (default: True)

    Returns:
        A requests.Session with Cloudflare cookies, or None if failed
    """
    try:
        from playwright.sync_api import sync_playwright
        from playwright_stealth import stealth_sync
    except ImportError:
        logger.warning("Playwright not available, skipping browser fallback")
        return None

    base_url = base_url.rstrip("/")
    session = requests.Session()
    session.headers.update(BROWSER_HEADERS)

    try:
        with sync_playwright() as p:
            # Launch browser with stealth settings
            browser = p.chromium.launch(
                headless=headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-infobars",
                    "--window-size=1920,1080",
                    "--start-maximized",
                ],
            )

            # Create context with realistic viewport and user agent
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="en-US",
                timezone_id="America/New_York",
            )

            page = context.new_page()

            # Apply stealth to avoid detection
            stealth_sync(page)

            # Navigate to the site and wait for Cloudflare challenge to complete
            logger.info(f"Playwright: Navigating to {base_url}")
            page.goto(base_url, wait_until="networkidle", timeout=timeout_seconds * 1000)

            # Wait additional time for any JS challenges
            page.wait_for_timeout(3000)

            # Check if we got past Cloudflare
            content = page.content().lower()
            if "cloudflare" in content and ("challenge" in content or "checking" in content):
                # Wait longer for challenge to complete
                logger.info("Playwright: Waiting for Cloudflare challenge...")
                page.wait_for_timeout(5000)

            # Get cookies from browser
            cookies = context.cookies()
            logger.info(f"Playwright: Got {len(cookies)} cookies")

            # Transfer cookies to requests session
            for cookie in cookies:
                session.cookies.set(
                    cookie["name"],
                    cookie["value"],
                    domain=cookie.get("domain", ""),
                    path=cookie.get("path", "/"),
                )

            # Get the user agent used
            user_agent = page.evaluate("navigator.userAgent")
            session.headers["User-Agent"] = user_agent

            browser.close()

            # Test if session works
            test_resp = session.get(
                f"{base_url}/",
                timeout=timeout_seconds,
                allow_redirects=True,
            )

            if test_resp.status_code == 200:
                logger.info("Playwright: Session created successfully")
                return session
            else:
                logger.warning(f"Playwright: Test request got status {test_resp.status_code}")
                return None

    except Exception as e:
        logger.error(f"Playwright fallback failed: {e}")
        return None


def create_cloudflare_session_with_fallback(
    base_url: str,
    timeout_seconds: float = 15.0,
    use_curl_cffi: bool = True,
    use_playwright_fallback: bool = True,
) -> requests.Session:
    """Create a session with Cloudflare bypass, trying multiple strategies.

    Order of attempts:
    1. cloudscraper with different browser profiles
    2. curl_cffi with real browser TLS fingerprints
    3. Playwright with stealth (real browser)

    Args:
        base_url: The base URL to test against
        timeout_seconds: Timeout for test requests
        use_curl_cffi: Try curl_cffi before Playwright (default: True)
        use_playwright_fallback: Use Playwright as final fallback (default: True)

    Returns:
        A session configured to bypass Cloudflare
    """
    base_url = base_url.rstrip("/")

    # Strategy 1: Try cloudscraper with different profiles
    logger.info("Trying cloudscraper profiles...")
    for profile in BROWSER_PROFILES:
        try:
            session = cloudscraper.create_scraper(
                browser=profile,
                delay=3,
            )
            session.headers.update(BROWSER_HEADERS)

            test_resp = session.get(
                f"{base_url}/",
                timeout=timeout_seconds,
                allow_redirects=True,
            )
            if test_resp.status_code == 200:
                logger.info(f"Cloudflare bypass successful with cloudscraper profile: {profile}")
                return session
            elif test_resp.status_code == 403:
                logger.warning(f"Cloudscraper profile {profile} got 403, trying next...")
                continue
        except Exception as e:
            logger.warning(f"Cloudscraper profile {profile} failed: {e}, trying next...")
            continue

    # Strategy 2: Try curl_cffi with TLS fingerprinting
    if use_curl_cffi:
        logger.info("Cloudscraper failed, trying curl_cffi with TLS fingerprints...")
        curl_session = _create_session_with_curl_cffi(base_url, timeout_seconds)
        if curl_session is not None:
            return curl_session  # type: ignore

    # Strategy 3: Try Playwright with stealth
    if use_playwright_fallback:
        logger.info("curl_cffi failed, trying Playwright with stealth...")
        playwright_session = _create_session_with_playwright(
            base_url,
            timeout_seconds=30.0,
            headless=True,
        )
        if playwright_session is not None:
            return playwright_session

    # Ultimate fallback: return cloudscraper session even if it didn't work
    logger.warning("All bypass methods failed, using basic cloudscraper as fallback")
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
