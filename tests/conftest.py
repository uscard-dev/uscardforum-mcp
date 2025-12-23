"""
Pytest configuration and fixtures for integration tests.

These tests run against the actual USCardForum API.

Required environment variables:
    NITAN_USERNAME: Forum username for authenticated tests
    NITAN_PASSWORD: Forum password for authenticated tests
"""

import os
import pytest

# Skip Playwright browser installation in tests (too slow)
os.environ.setdefault("NITAN_SKIP_PLAYWRIGHT", "true")

from uscardforum.client import DiscourseClient


# Test credentials from environment (required)
NITAN_USERNAME = os.environ.get("NITAN_USERNAME")
NITAN_PASSWORD = os.environ.get("NITAN_PASSWORD")


@pytest.fixture(scope="session")
def client():
    """Create a DiscourseClient instance for testing."""
    return DiscourseClient()


@pytest.fixture(scope="session")
def authenticated_client():
    """Create an authenticated DiscourseClient instance."""
    if not NITAN_USERNAME or not NITAN_PASSWORD:
        pytest.skip("NITAN_USERNAME and NITAN_PASSWORD env vars required")

    client = DiscourseClient()
    result = client.login(NITAN_USERNAME, NITAN_PASSWORD)
    if not result.success:
        pytest.skip(f"Could not authenticate: {result.error}")
    return client


@pytest.fixture(scope="session")
def test_username():
    """Return the test username."""
    if not NITAN_USERNAME:
        pytest.skip("NITAN_USERNAME env var required")
    return NITAN_USERNAME


@pytest.fixture(scope="session")
def test_password():
    """Return the test password."""
    if not NITAN_PASSWORD:
        pytest.skip("NITAN_PASSWORD env var required")
    return NITAN_PASSWORD
