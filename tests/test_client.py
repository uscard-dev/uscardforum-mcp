"""
Integration tests for DiscourseClient.

Tests the main client interface against the actual USCardForum API.
"""

import pytest
from uscardforum.client import DiscourseClient
from uscardforum.models.topics import TopicSummary, TopicInfo, Post
from uscardforum.models.users import UserSummary, UserBadges, FollowList
from uscardforum.models.search import SearchResult
from uscardforum.models.categories import CategoryMap
from uscardforum.models.auth import Session, LoginResult


class TestDiscourseClientInit:
    """Tests for client initialization."""

    def test_default_initialization(self):
        """Test client initializes with default base URL."""
        client = DiscourseClient()
        assert client.base_url == "https://www.uscardforum.com"

    def test_custom_base_url(self):
        """Test client accepts custom base URL."""
        custom_url = "https://example.com"
        client = DiscourseClient(base_url=custom_url)
        assert client.base_url == custom_url

    def test_client_has_base_url_property(self):
        """Test client exposes base_url property."""
        client = DiscourseClient()
        assert hasattr(client, "base_url")
        assert client.base_url == "https://www.uscardforum.com"

    def test_client_has_is_authenticated_property(self):
        """Test client has is_authenticated property."""
        client = DiscourseClient()
        assert hasattr(client, "is_authenticated")
        assert client.is_authenticated is False


class TestClientTopicMethods:
    """Test client topic-related methods return correct types."""

    def test_get_hot_topics_returns_topic_summaries(self, client):
        """Test get_hot_topics returns list of TopicSummary."""
        topics = client.get_hot_topics()

        assert isinstance(topics, list)
        assert len(topics) > 0
        assert all(isinstance(t, TopicSummary) for t in topics)

    def test_get_new_topics_returns_topic_summaries(self, client):
        """Test get_new_topics returns list of TopicSummary."""
        topics = client.get_new_topics()

        assert isinstance(topics, list)
        assert len(topics) > 0
        assert all(isinstance(t, TopicSummary) for t in topics)

    def test_get_top_topics_returns_topic_summaries(self, client):
        """Test get_top_topics returns list of TopicSummary."""
        topics = client.get_top_topics()

        assert isinstance(topics, list)
        assert len(topics) > 0
        assert all(isinstance(t, TopicSummary) for t in topics)

    def test_get_topic_info_returns_topic_info(self, client):
        """Test get_topic_info returns TopicInfo."""
        hot = client.get_hot_topics()
        topic_id = hot[0].id
        info = client.get_topic_info(topic_id)

        assert isinstance(info, TopicInfo)
        assert info.topic_id == topic_id, "topic_id must match requested ID"
        assert info.post_count >= 1, "post_count must be at least 1"

    def test_get_topic_posts_returns_post_list(self, client):
        """Test get_topic_posts returns list of Post."""
        hot = client.get_hot_topics()
        posts = client.get_topic_posts(hot[0].id)

        assert isinstance(posts, list)
        assert len(posts) > 0
        assert all(isinstance(p, Post) for p in posts)

    def test_get_all_topic_posts_returns_post_list(self, client):
        """Test get_all_topic_posts returns list of Post."""
        hot = client.get_hot_topics()
        posts = client.get_all_topic_posts(hot[0].id, max_posts=5)

        assert isinstance(posts, list)
        assert len(posts) <= 5
        assert all(isinstance(p, Post) for p in posts)


class TestClientUserMethods:
    """Test client user-related methods return correct types."""

    def test_get_user_summary_returns_user_summary(self, client, test_username):
        """Test get_user_summary returns UserSummary."""
        summary = client.get_user_summary(test_username)

        assert isinstance(summary, UserSummary)
        assert summary.username == test_username
        assert summary.stats is not None

    def test_get_user_badges_returns_user_badges(self, client, test_username):
        """Test get_user_badges returns UserBadges."""
        badges = client.get_user_badges(test_username)

        assert isinstance(badges, UserBadges)
        assert isinstance(badges.badges, list)

    def test_list_user_badges_returns_strings(self, client, test_username):
        """Test list_user_badges returns list of strings."""
        names = client.list_user_badges(test_username)

        assert isinstance(names, list)
        assert all(isinstance(n, str) for n in names)

    def test_get_user_following_returns_follow_list(self, client, test_username):
        """Test get_user_following returns FollowList."""
        following = client.get_user_following(test_username)

        assert isinstance(following, FollowList)
        assert isinstance(following.users, list)
        assert isinstance(following.total_count, int)

    def test_get_user_followers_returns_follow_list(self, client, test_username):
        """Test get_user_followers returns FollowList."""
        followers = client.get_user_followers(test_username)

        assert isinstance(followers, FollowList)


class TestClientSearchMethods:
    """Test client search methods return correct types."""

    def test_search_returns_search_result(self, client):
        """Test search returns SearchResult."""
        result = client.search("credit")

        assert isinstance(result, SearchResult)
        assert isinstance(result.posts, list)
        assert isinstance(result.topics, list)

    def test_search_with_order(self, client):
        """Test search with order parameter."""
        result = client.search("credit", order="latest")

        assert isinstance(result, SearchResult)


class TestClientCategoryMethods:
    """Test client category methods return correct types."""

    def test_get_category_map_returns_category_map(self, client):
        """Test get_category_map returns CategoryMap."""
        category_map = client.get_category_map()

        assert isinstance(category_map, CategoryMap)
        assert len(category_map.categories) > 0


class TestClientAuthFlow:
    """Test client authentication workflow."""

    def test_login_returns_login_result(self, client, test_username, test_password):
        """Test login returns LoginResult."""
        result = client.login(test_username, test_password)

        assert isinstance(result, LoginResult)
        assert result.success is True
        assert result.username == test_username

    def test_get_current_session_returns_session(self, client):
        """Test get_current_session returns Session."""
        session = client.get_current_session()

        assert isinstance(session, Session)
        assert isinstance(session.is_authenticated, bool)

    def test_full_auth_flow(self, test_username, test_password):
        """Test complete authentication flow."""
        # Create fresh client
        client = DiscourseClient()

        # Initially not authenticated
        session = client.get_current_session()
        assert session.is_authenticated is False

        # Login
        login_result = client.login(test_username, test_password)
        assert login_result.success is True

        # Now authenticated
        session = client.get_current_session()
        assert session.is_authenticated is True
        assert session.current_user is not None
        assert session.current_user.username == test_username


class TestClientMethodChaining:
    """Test that client methods can be chained together."""

    def test_get_topic_then_posts(self, client):
        """Test getting topic info then posts."""
        hot = client.get_hot_topics()
        topic_id = hot[0].id

        info = client.get_topic_info(topic_id)
        posts = client.get_topic_posts(topic_id)

        assert info.topic_id == topic_id, "Topic ID should match"
        assert len(posts) >= 1, "Should have posts"
        assert posts[0].post_number == 1, "First post should be number 1"

    def test_search_then_get_topic(self, client):
        """Test searching then getting topic posts."""
        result = client.search("Chase")

        if len(result.topics) > 0:
            topic_id = result.topics[0].id
            posts = client.get_topic_posts(topic_id)

            assert isinstance(posts, list)
            assert len(posts) > 0
            assert posts[0].post_number >= 1
