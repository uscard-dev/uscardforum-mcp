"""Cloudflare bypass utilities.

Provides functions and constants for bypassing Cloudflare protection
using multiple strategies in order:
1. cloudscraper (multiple browser profiles - fastest)
2. curl_cffi (real browser TLS fingerprints)
3. Playwright with stealth (real browser - most effective but slowest)
"""
from __future__ import annotations

import logging
import os
import subprocess
import time
from typing import Any

import cloudscraper
import requests

logger = logging.getLogger(__name__)

# Environment variable to skip Playwright (useful for tests/CI)
SKIP_PLAYWRIGHT = os.environ.get("NITAN_SKIP_PLAYWRIGHT", "").lower() in ("true", "1", "yes")

# Track if we've already tried to install Playwright browsers
_playwright_browsers_installed = False

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
# Note: We don't advertise 'br' (brotli) since the brotli package may not be installed
BROWSER_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}


def _ensure_playwright_browsers(skip_install: bool = False) -> bool:
    """Ensure Playwright browsers are installed.

    Attempts to install Chromium if not already installed.
    Only tries once per process to avoid repeated installation attempts.

    Args:
        skip_install: If True, skip browser installation attempts (for tests/CI)

    Returns:
        True if browsers are available, False otherwise
    """
    global _playwright_browsers_installed

    if _playwright_browsers_installed:
        return True

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.warning("Playwright package not installed")
        return False

    # Try to launch browser to check if it's installed
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
            _playwright_browsers_installed = True
            logger.info("Playwright browsers already installed")
            return True
    except Exception as e:
        logger.info(f"Playwright browsers not installed: {e}")
        if skip_install:
            logger.info("Skipping browser installation (skip_install=True)")
            return False

    # Try to install browsers
    try:
        logger.info("Installing Playwright Chromium browser...")
        result = subprocess.run(
            ["playwright", "install", "chromium"],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )
        if result.returncode == 0:
            logger.info("Playwright Chromium installed successfully")
            _playwright_browsers_installed = True
            return True
        else:
            logger.warning(f"Playwright install failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        logger.warning("Playwright installation timed out")
        return False
    except FileNotFoundError:
        logger.warning("playwright command not found")
        return False
    except Exception as e:
        logger.warning(f"Failed to install Playwright browsers: {e}")
        return False


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
    session: Any = cloudscraper.create_scraper(
        browser={"browser": browser, "platform": platform, "desktop": True},
        delay=delay,
    )
    session.headers.update(BROWSER_HEADERS)
    return session  # type: ignore[no-any-return]


class CurlCffiSessionWrapper:
    """Wrapper to make curl_cffi.Session behave like requests.Session.

    This allows curl_cffi to be used as a drop-in replacement.
    """

    def __init__(self, session: Any = None, impersonate: str = "chrome120"):
        """Initialize wrapper with existing session or create new one.

        Args:
            session: Existing curl_cffi Session to wrap (reuses cookies)
            impersonate: Browser to impersonate if creating new session
        """
        if session is not None:
            self._session = session
        else:
            from curl_cffi.requests import Session
            self._session = Session(impersonate=impersonate)  # type: ignore[arg-type]
        self._impersonate = impersonate
        self.headers = dict(BROWSER_HEADERS)
        self.cookies = self._session.cookies

    def get(self, url: str, **kwargs: Any) -> Any:
        """Make GET request."""
        kwargs.setdefault("timeout", 15)
        # Merge headers
        headers = dict(self.headers)
        if "headers" in kwargs:
            headers.update(kwargs["headers"])
        kwargs["headers"] = headers
        return self._session.get(url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> Any:
        """Make POST request."""
        kwargs.setdefault("timeout", 15)
        headers = dict(self.headers)
        if "headers" in kwargs:
            headers.update(kwargs["headers"])
        kwargs["headers"] = headers
        return self._session.post(url, **kwargs)

    def request(self, method: str, url: str, **kwargs: Any) -> Any:
        """Make any HTTP request."""
        kwargs.setdefault("timeout", 15)
        headers = dict(self.headers)
        if "headers" in kwargs:
            headers.update(kwargs["headers"])
        kwargs["headers"] = headers
        return self._session.request(method, url, **kwargs)


def _create_session_with_curl_cffi(
    base_url: str,
    timeout_seconds: float = 15.0,
) -> Any | None:
    """Create a session using curl_cffi with browser TLS fingerprints.

    curl_cffi impersonates real browser TLS fingerprints, which is very
    effective against Cloudflare's TLS fingerprinting.

    Args:
        base_url: The base URL to test against
        timeout_seconds: Timeout for test requests

    Returns:
        A curl_cffi session wrapper (reusing the session that passed), or None if failed
    """
    try:
        from curl_cffi.requests import Session
    except ImportError:
        logger.warning("curl_cffi not available, skipping TLS fingerprint bypass")
        return None

    base_url = base_url.rstrip("/")

    for impersonate in CURL_CFFI_IMPERSONATES:
        try:
            session: Any = Session(impersonate=impersonate)  # type: ignore[arg-type]

            # Test if this impersonation works
            test_resp = session.get(
                f"{base_url}/",
                timeout=timeout_seconds,
                allow_redirects=True,
            )

            if test_resp.status_code == 200:
                logger.info(f"Cloudflare bypass successful with curl_cffi impersonate={impersonate}")
                # IMPORTANT: Return wrapper with the SAME session that passed (keeps cookies!)
                wrapper = CurlCffiSessionWrapper(session=session, impersonate=impersonate)
                return wrapper
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
    skip_install: bool = False,
) -> requests.Session | None:
    """Create a requests session using cookies obtained from Playwright with stealth.

    Uses a real browser to solve Cloudflare challenges and transfers cookies
    to a requests session. Will attempt to install browsers if not present.

    Args:
        base_url: The base URL to navigate to
        timeout_seconds: Timeout for page load
        headless: Run browser in headless mode (default: True)
        skip_install: Skip browser installation attempts (for tests/CI)

    Returns:
        A requests.Session with Cloudflare cookies, or None if failed
    """
    # Ensure browsers are installed (this also verifies imports work)
    if not _ensure_playwright_browsers(skip_install=skip_install):
        logger.warning("Playwright browsers not available")
        return None

    base_url = base_url.rstrip("/")
    session = requests.Session()
    session.headers.update(BROWSER_HEADERS)

    try:
        # Import here after ensuring browsers are installed
        from playwright.sync_api import sync_playwright
        from playwright_stealth import Stealth

        stealth = Stealth()

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
            stealth.apply_stealth_sync(page)

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

    except ImportError as e:
        logger.warning(f"Playwright import failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Playwright fallback failed: {e}")
        return None


def create_cloudflare_session_with_fallback(
    base_url: str,
    timeout_seconds: float = 15.0,
    use_cloudscraper: bool = True,
    use_curl_cffi: bool = True,
    use_playwright: bool = True,
) -> Any:
    """Create a session with Cloudflare bypass, trying multiple strategies.

    Order of attempts (fastest first):
    1. cloudscraper with different browser profiles (fastest)
    2. curl_cffi with real browser TLS fingerprints
    3. Playwright with stealth (real browser - most effective but slowest)

    Args:
        base_url: The base URL to test against
        timeout_seconds: Timeout for test requests
        use_cloudscraper: Try cloudscraper first (default: True)
        use_curl_cffi: Try curl_cffi (default: True)
        use_playwright: Try Playwright last (default: True)

    Returns:
        A session configured to bypass Cloudflare
    """
    base_url = base_url.rstrip("/")

    # Strategy 1: Try cloudscraper with different profiles (fastest)
    if use_cloudscraper:
        logger.info("Trying cloudscraper profiles (fastest)...")
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
        logger.warning("cloudscraper failed, trying next strategy...")

    # Strategy 2: Try curl_cffi with TLS fingerprinting
    if use_curl_cffi:
        logger.info("Trying curl_cffi with TLS fingerprints...")
        curl_session = _create_session_with_curl_cffi(base_url, timeout_seconds)
        if curl_session is not None:
            return curl_session
        logger.warning("curl_cffi failed, trying next strategy...")

    # Strategy 3: Try Playwright with stealth (most effective but slowest)
    if use_playwright and not SKIP_PLAYWRIGHT:
        logger.info("Trying Playwright with stealth (most effective)...")
        playwright_session = _create_session_with_playwright(
            base_url,
            timeout_seconds=30.0,
            headless=True,
            skip_install=True,  # Never auto-install during session creation
        )
        if playwright_session is not None:
            return playwright_session
        logger.warning("Playwright failed...")
    elif SKIP_PLAYWRIGHT:
        logger.info("Playwright skipped (NITAN_SKIP_PLAYWRIGHT=true)")

    # Ultimate fallback: return cloudscraper session even if it didn't work
    logger.warning("All bypass methods failed, using basic cloudscraper as fallback")
    session = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "linux", "desktop": True},
        delay=5,
    )
    session.headers.update(BROWSER_HEADERS)
    return session


def warm_up_session(
    session: Any,
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
        except Exception as e:
            logger.warning(f"Warm-up failed for {url}: {e}")

    return success


def extended_warm_up(
    session: Any,
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
        except Exception as e:
            logger.warning(f"Warm-up failed for {url}: {e}")


def is_cloudflare_challenge(response: Any) -> bool:
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
