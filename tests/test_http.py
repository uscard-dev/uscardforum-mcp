"""
Integration tests for HTTP utilities.

Tests the HTTP functions against the actual USCardForum API.
"""

import pytest
import cloudscraper
from uscardforum.utils.http import full_url, request_json, parse_json_or_raise


BASE_URL = "https://www.uscardforum.com"
TIMEOUT = 30.0


class TestFullUrlFunction:
    """Tests for full_url utility function."""

    def test_full_url_with_relative_path(self):
        """Test URL construction with relative path."""
        url = full_url(BASE_URL, "/hot.json")
        assert url == "https://www.uscardforum.com/hot.json"

    def test_full_url_with_custom_base(self):
        """Test URL construction with custom base URL."""
        url = full_url("https://example.com", "/test")
        assert url == "https://example.com/test"

    def test_full_url_preserves_absolute_url(self):
        """Test that absolute URLs are preserved unchanged."""
        absolute = "https://other.com/path"
        url = full_url(BASE_URL, absolute)
        assert url == absolute

    def test_full_url_with_query_params(self):
        """Test URL with query parameters."""
        url = full_url(BASE_URL, "/search.json?q=test")
        assert url == "https://www.uscardforum.com/search.json?q=test"

    def test_full_url_with_path_segments(self):
        """Test URL with multiple path segments."""
        url = full_url(BASE_URL, "/u/username/summary.json")
        assert url == "https://www.uscardforum.com/u/username/summary.json"


class TestParseJsonOrRaise:
    """Tests for parse_json_or_raise utility function."""

    def test_parse_valid_json(self):
        """Test parsing valid JSON response."""

        class MockResponse:
            def json(self):
                return {"key": "value", "number": 42}

            headers = {"Content-Type": "application/json"}
            text = '{"key": "value", "number": 42}'

        result = parse_json_or_raise(MockResponse())

        assert result == {"key": "value", "number": 42}
        assert isinstance(result, dict)

    def test_parse_json_array(self):
        """Test parsing JSON array response."""

        class MockResponse:
            def json(self):
                return [1, 2, 3]

            headers = {"Content-Type": "application/json"}
            text = '[1, 2, 3]'

        result = parse_json_or_raise(MockResponse())

        assert result == [1, 2, 3]
        assert isinstance(result, list)

    def test_parse_invalid_json_raises(self):
        """Test parsing invalid JSON raises RuntimeError."""

        class MockResponse:
            def json(self):
                raise ValueError("No JSON object could be decoded")

            headers = {"Content-Type": "text/html"}
            text = "not valid json {"

        with pytest.raises(RuntimeError) as exc_info:
            parse_json_or_raise(MockResponse())

        assert "Expected JSON" in str(exc_info.value)

    def test_parse_empty_object(self):
        """Test parsing empty JSON object."""

        class MockResponse:
            def json(self):
                return {}

            headers = {"Content-Type": "application/json"}
            text = "{}"

        result = parse_json_or_raise(MockResponse())
        assert result == {}

    def test_parse_nested_json(self):
        """Test parsing nested JSON structure."""

        class MockResponse:
            def json(self):
                return {"outer": {"inner": {"deep": True}}}

            headers = {"Content-Type": "application/json"}
            text = '{"outer": {"inner": {"deep": true}}}'

        result = parse_json_or_raise(MockResponse())

        assert result["outer"]["inner"]["deep"] is True


class TestRequestJsonIntegration:
    """Integration tests for request_json against real API."""

    @pytest.fixture
    def session(self):
        """Create cloudscraper session for tests."""
        return cloudscraper.create_scraper()

    def test_request_hot_topics(self, session):
        """Test fetching hot topics JSON endpoint."""
        data = request_json(session, "GET", BASE_URL, "/hot.json", timeout_seconds=TIMEOUT)

        assert isinstance(data, dict)
        assert "topic_list" in data, "Response should have topic_list"
        assert "topics" in data["topic_list"], "topic_list should have topics"

    def test_request_new_topics(self, session):
        """Test fetching new topics JSON endpoint."""
        data = request_json(session, "GET", BASE_URL, "/new.json", timeout_seconds=TIMEOUT)

        assert isinstance(data, dict)
        assert "topic_list" in data

    def test_request_categories(self, session):
        """Test fetching categories JSON endpoint."""
        data = request_json(session, "GET", BASE_URL, "/categories.json", timeout_seconds=TIMEOUT)

        assert isinstance(data, dict)
        assert "category_list" in data, "Response should have category_list"
        assert "categories" in data["category_list"]

    def test_request_search(self, session):
        """Test search JSON endpoint."""
        data = request_json(session, "GET", BASE_URL, "/search.json", timeout_seconds=TIMEOUT, params={"q": "credit"})

        assert isinstance(data, dict)
        # Search should return posts or topics
        assert "posts" in data or "topics" in data

    def test_request_user_summary(self, session):
        """Test fetching user summary JSON."""
        data = request_json(session, "GET", BASE_URL, "/u/system/summary.json", timeout_seconds=TIMEOUT)

        assert isinstance(data, dict)
        assert "user_summary" in data, "Response should have user_summary"

    def test_request_topic_json(self, session):
        """Test fetching a topic JSON endpoint."""
        # First get a topic ID
        hot_data = request_json(session, "GET", BASE_URL, "/hot.json", timeout_seconds=TIMEOUT)
        topics = hot_data["topic_list"]["topics"]
        assert len(topics) > 0

        topic_id = topics[0]["id"]
        data = request_json(session, "GET", BASE_URL, f"/t/{topic_id}.json", timeout_seconds=TIMEOUT)

        assert isinstance(data, dict)
        assert "id" in data, "Topic response should have id"
        assert data["id"] == topic_id

    def test_request_returns_valid_topic_structure(self, session):
        """Test that topic response has expected structure."""
        hot_data = request_json(session, "GET", BASE_URL, "/hot.json", timeout_seconds=TIMEOUT)
        topic_id = hot_data["topic_list"]["topics"][0]["id"]

        data = request_json(session, "GET", BASE_URL, f"/t/{topic_id}.json", timeout_seconds=TIMEOUT)

        # Verify expected topic fields
        assert "id" in data
        assert "title" in data
        assert "posts_count" in data
        assert "post_stream" in data
        assert "posts" in data["post_stream"]

    def test_request_with_query_params(self, session):
        """Test request with query parameters."""
        data = request_json(session, "GET", BASE_URL, "/top.json", timeout_seconds=TIMEOUT, params={"period": "weekly"})

        assert isinstance(data, dict)
        assert "topic_list" in data
