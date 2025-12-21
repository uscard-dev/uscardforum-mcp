"""
Integration tests for Search API.

Tests against the actual USCardForum API with comprehensive field assertions.
"""

import pytest
from datetime import datetime
from uscardforum.models.search import (
    SearchResult,
    SearchPost,
    SearchTopic,
    SearchUser,
    GroupedSearchResult,
)


class TestSearchResultModel:
    """Test SearchResult model fields are populated correctly."""

    def test_search_result_structure(self, client):
        """Test SearchResult has correct structure."""
        result = client.search("credit card")

        assert isinstance(result, SearchResult)

        # Ensure JSON output keys are covered by the SearchResult domain model
        result_keys = set(result.model_dump().keys())
        model_keys = set(SearchResult.model_fields.keys())
        assert result_keys.issubset(model_keys)

        assert isinstance(result.posts, list), "posts must be list"
        assert isinstance(result.topics, list), "topics must be list"
        assert isinstance(result.users, list), "users must be list"

    def test_search_returns_results_for_common_term(self, client):
        """Test search for common term returns results."""
        result = client.search("Chase")

        assert isinstance(result, SearchResult)
        # Chase is very common on a credit card forum
        has_results = len(result.posts) > 0 or len(result.topics) > 0
        assert has_results, "Common term should return results"


class TestSearchPostModel:
    """Test SearchPost model fields are populated correctly."""

    def test_search_post_required_fields(self, client):
        """Test SearchPost required fields."""
        result = client.search("credit")

        if len(result.posts) > 0:
            post = result.posts[0]
            assert isinstance(post, SearchPost)

            post_keys = set(post.model_dump().keys())
            model_keys = set(SearchPost.model_fields.keys())
            assert post_keys.issubset(model_keys)

            # Required fields
            assert post.id > 0, "id must be positive"
            assert post.topic_id > 0, "topic_id must be positive"
            assert post.post_number >= 1, "post_number must be at least 1"

    def test_search_post_optional_fields(self, client):
        """Test SearchPost optional fields."""
        result = client.search("credit")

        if len(result.posts) > 0:
            post = result.posts[0]

            # Username
            if post.username is not None:
                assert isinstance(post.username, str)
                assert len(post.username) > 0

            # Blurb (excerpt)
            if post.blurb is not None:
                assert isinstance(post.blurb, str)

            # Timestamp
            if post.created_at is not None:
                assert isinstance(post.created_at, datetime)

    def test_search_post_like_count(self, client):
        """Test SearchPost like_count is non-negative."""
        result = client.search("credit")

        if len(result.posts) > 0:
            post = result.posts[0]
            assert post.like_count >= 0, "like_count must be non-negative"

    def test_multiple_search_posts_valid(self, client):
        """Test multiple search posts are valid."""
        result = client.search("bank account")

        for post in result.posts[:10]:
            assert isinstance(post, SearchPost)
            assert post.id > 0
            assert post.topic_id > 0
            assert post.post_number >= 1


class TestSearchTopicModel:
    """Test SearchTopic model fields are populated correctly."""

    def test_search_topic_required_fields(self, client):
        """Test SearchTopic required fields."""
        result = client.search("credit")

        if len(result.topics) > 0:
            topic = result.topics[0]
            assert isinstance(topic, SearchTopic)

            topic_keys = set(topic.model_dump().keys())
            model_keys = set(SearchTopic.model_fields.keys())
            assert topic_keys.issubset(model_keys)

            # Required fields
            assert topic.id > 0, "id must be positive"
            assert topic.title, "title must not be empty"
            assert isinstance(topic.title, str)

    def test_search_topic_count_fields(self, client):
        """Test SearchTopic count fields are non-negative."""
        result = client.search("credit")

        if len(result.topics) > 0:
            topic = result.topics[0]

            assert topic.posts_count >= 0, "posts_count must be non-negative"
            assert topic.views >= 0, "views must be non-negative"
            assert topic.like_count >= 0, "like_count must be non-negative"

    def test_search_topic_optional_fields(self, client):
        """Test SearchTopic optional fields."""
        result = client.search("credit")

        if len(result.topics) > 0:
            topic = result.topics[0]

            if topic.category_id is not None:
                assert topic.category_id > 0

            if topic.created_at is not None:
                assert isinstance(topic.created_at, datetime)


class TestSearchUserModel:
    """Test SearchUser model fields are populated correctly."""

    def test_search_users_structure(self, client):
        """Test search result users are valid SearchUser objects."""
        result = client.search("credit")

        for user in result.users[:5]:
            assert isinstance(user, SearchUser)

    def test_search_user_required_fields(self, client):
        """Test SearchUser required fields when present."""
        result = client.search("admin")  # More likely to match users

        if len(result.users) > 0:
            user = result.users[0]
            assert isinstance(user, SearchUser)

            user_keys = set(user.model_dump().keys())
            model_keys = set(SearchUser.model_fields.keys())
            assert user_keys.issubset(model_keys)

            assert user.id > 0, "id must be positive"
            assert user.username, "username must not be empty"
            assert isinstance(user.username, str)


class TestGroupedSearchResultModel:
    """Test GroupedSearchResult model fields are populated correctly."""

    def test_grouped_search_metadata_structure(self, client):
        """Test GroupedSearchResult metadata when present."""
        result = client.search("amex")

        assert isinstance(result, SearchResult)

        # grouped_search_result contains metadata about the search
        if result.grouped_search_result is not None:
            grouped = result.grouped_search_result
            assert isinstance(grouped, GroupedSearchResult)

            assert isinstance(grouped.post_ids, list)
            assert isinstance(grouped.topic_ids, list)
            assert isinstance(grouped.user_ids, list)

    def test_grouped_search_ids_are_positive(self, client):
        """Test grouped search IDs are positive integers."""
        result = client.search("credit")

        if result.grouped_search_result is not None:
            grouped = result.grouped_search_result

            for post_id in grouped.post_ids:
                assert post_id > 0, "post_id must be positive"

            for topic_id in grouped.topic_ids:
                assert topic_id > 0, "topic_id must be positive"

    def test_grouped_more_flags(self, client):
        """Test GroupedSearchResult more_posts/more_topics flags."""
        result = client.search("credit")

        if result.grouped_search_result is not None:
            grouped = result.grouped_search_result

            # These are optional boolean flags
            if grouped.more_posts is not None:
                assert isinstance(grouped.more_posts, bool)
            if grouped.more_topics is not None:
                assert isinstance(grouped.more_topics, bool)


class TestSearchOrdering:
    """Test search ordering options."""

    def test_search_order_latest(self, client):
        """Test search with latest ordering."""
        result = client.search("credit", order="latest")

        assert isinstance(result, SearchResult)

    def test_search_order_likes(self, client):
        """Test search with likes ordering."""
        result = client.search("credit", order="likes")

        assert isinstance(result, SearchResult)

    def test_search_order_views(self, client):
        """Test search with views ordering."""
        result = client.search("credit", order="views")

        assert isinstance(result, SearchResult)


class TestSearchOperators:
    """Test Discourse search operators."""

    def test_search_in_title(self, client):
        """Test search with in:title operator."""
        result = client.search("Chase in:title")

        assert isinstance(result, SearchResult)
        # Results should be topic titles containing Chase
        for topic in result.topics[:5]:
            # Title should contain search term (case insensitive)
            assert "chase" in topic.title.lower() or len(result.posts) > 0

    def test_search_empty_results(self, client):
        """Test search with unlikely term returns empty results."""
        result = client.search("xyznonexistent12345abcde")

        assert isinstance(result, SearchResult)
        # Should have no or minimal results
        total = len(result.posts) + len(result.topics)
        assert total == 0, "Nonsense query should have no results"
