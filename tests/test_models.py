"""
Integration tests for Pydantic models.

Tests that all model fields are correctly typed and populated from real API data.
"""

import pytest
from datetime import datetime
from uscardforum.client import DiscourseClient
from uscardforum.models.topics import TopicSummary, TopicInfo, Post
from uscardforum.models.users import (
    UserSummary,
    UserStats,
    UserAction,
    Badge,
    UserBadges,
    FollowUser,
    FollowList,
)
from uscardforum.models.search import SearchResult, SearchPost, SearchTopic, GroupedSearchResult
from uscardforum.models.categories import Category
from uscardforum.models.auth import Session, CurrentUser, LoginResult


class TestTopicModelsFieldTypes:
    """Test topic model field types match expected types."""

    def test_topic_summary_field_types(self, client):
        """Test TopicSummary fields have correct types."""
        topics = client.get_hot_topics()
        topic = topics[0]

        # Required fields
        assert isinstance(topic.id, int)
        assert isinstance(topic.title, str)

        # Default fields
        assert isinstance(topic.posts_count, int)
        assert isinstance(topic.views, int)
        assert isinstance(topic.like_count, int)

        # Optional fields (check type when present)
        if topic.category_id is not None:
            assert isinstance(topic.category_id, int)
        if topic.created_at is not None:
            assert isinstance(topic.created_at, datetime)
        if topic.last_posted_at is not None:
            assert isinstance(topic.last_posted_at, datetime)

    def test_topic_info_field_types(self, client):
        """Test TopicInfo fields have correct types."""
        hot = client.get_hot_topics()
        topic_id = hot[0].id
        info = client.get_topic_info(topic_id)

        # Required fields
        assert isinstance(info.topic_id, int)
        assert info.topic_id == topic_id
        assert isinstance(info.post_count, int)
        assert isinstance(info.highest_post_number, int)

        # Optional fields
        if info.title is not None:
            assert isinstance(info.title, str)
        if info.last_posted_at is not None:
            assert isinstance(info.last_posted_at, datetime)

    def test_post_field_types(self, client):
        """Test Post fields have correct types."""
        hot = client.get_hot_topics()
        posts = client.get_topic_posts(hot[0].id)
        post = posts[0]

        # Required fields
        assert isinstance(post.id, int)
        assert post.id > 0
        assert isinstance(post.post_number, int)
        assert isinstance(post.username, str)
        assert isinstance(post.like_count, int)
        assert isinstance(post.reply_count, int)

        # Optional fields
        if post.cooked is not None:
            assert isinstance(post.cooked, str)
        if post.raw is not None:
            assert isinstance(post.raw, str)
        if post.created_at is not None:
            assert isinstance(post.created_at, datetime)
        if post.updated_at is not None:
            assert isinstance(post.updated_at, datetime)
        if post.reply_to_post_number is not None:
            assert isinstance(post.reply_to_post_number, int)

    def test_posts_list_field_types(self, client):
        """Test posts list from get_topic_posts has correct types."""
        hot = client.get_hot_topics()
        posts = client.get_topic_posts(hot[0].id)

        assert isinstance(posts, list), "Should return list"
        assert len(posts) > 0, "Should have posts"

        # Each post should be a Post object with correct types
        for post in posts[:3]:  # Check first 3
            assert isinstance(post, Post)
            assert isinstance(post.id, int)
            assert isinstance(post.post_number, int)
            assert isinstance(post.username, str)


class TestUserModelsFieldTypes:
    """Test user model field types match expected types."""

    def test_user_summary_field_types(self, client, test_username):
        """Test UserSummary fields have correct types."""
        summary = client.get_user_summary(test_username)

        if summary.user_id is not None:
            assert isinstance(summary.user_id, int)
        if summary.username is not None:
            assert isinstance(summary.username, str)
        if summary.name is not None:
            assert isinstance(summary.name, str)
        if summary.created_at is not None:
            assert isinstance(summary.created_at, datetime)
        if summary.last_seen_at is not None:
            assert isinstance(summary.last_seen_at, datetime)
        if summary.stats is not None:
            assert isinstance(summary.stats, UserStats)

        assert isinstance(summary.badges, list)
        assert isinstance(summary.top_topics, list)
        assert isinstance(summary.top_replies, list)

    def test_user_stats_field_types(self, client, test_username):
        """Test UserStats fields have correct types."""
        summary = client.get_user_summary(test_username)
        stats = summary.stats

        assert isinstance(stats.posts_read_count, int)
        assert isinstance(stats.topics_entered, int)
        assert isinstance(stats.likes_given, int)
        assert isinstance(stats.likes_received, int)
        assert isinstance(stats.days_visited, int)
        assert isinstance(stats.post_count, int)
        assert isinstance(stats.topic_count, int)

    def test_badge_field_types(self, client, test_username):
        """Test Badge fields have correct types."""
        badges = client.get_user_badges(test_username)

        if len(badges.badges) > 0:
            badge = badges.badges[0]

            assert isinstance(badge.id, int)
            assert isinstance(badge.badge_id, int)
            assert isinstance(badge.name, str)

            if badge.description is not None:
                assert isinstance(badge.description, str)
            if badge.granted_at is not None:
                assert isinstance(badge.granted_at, datetime)
            if badge.badge_type_id is not None:
                assert isinstance(badge.badge_type_id, int)

    def test_follow_list_field_types(self, client, test_username):
        """Test FollowList fields have correct types."""
        following = client.get_user_following(test_username)

        assert isinstance(following.users, list)
        assert isinstance(following.total_count, int)

        if len(following.users) > 0:
            user = following.users[0]
            assert isinstance(user, FollowUser)
            assert isinstance(user.id, int)
            assert isinstance(user.username, str)


class TestSearchModelsFieldTypes:
    """Test search model field types match expected types."""

    def test_search_result_field_types(self, client):
        """Test SearchResult fields have correct types."""
        result = client.search("credit")

        assert isinstance(result.posts, list)
        assert isinstance(result.topics, list)
        assert isinstance(result.users, list)

    def test_search_post_field_types(self, client):
        """Test SearchPost fields have correct types."""
        result = client.search("credit")

        if len(result.posts) > 0:
            post = result.posts[0]

            assert isinstance(post.id, int)
            assert isinstance(post.topic_id, int)
            assert isinstance(post.post_number, int)
            assert isinstance(post.like_count, int)

            if post.username is not None:
                assert isinstance(post.username, str)
            if post.blurb is not None:
                assert isinstance(post.blurb, str)
            if post.created_at is not None:
                assert isinstance(post.created_at, datetime)

    def test_search_topic_field_types(self, client):
        """Test SearchTopic fields have correct types."""
        result = client.search("credit")

        if len(result.topics) > 0:
            topic = result.topics[0]

            assert isinstance(topic.id, int)
            assert isinstance(topic.title, str)
            assert isinstance(topic.posts_count, int)
            assert isinstance(topic.views, int)
            assert isinstance(topic.like_count, int)

            if topic.category_id is not None:
                assert isinstance(topic.category_id, int)
            if topic.created_at is not None:
                assert isinstance(topic.created_at, datetime)


class TestCategoryModelsFieldTypes:
    """Test category model field types match expected types."""

    def test_category_field_types(self, client):
        """Test Category fields have correct types."""
        categories = client.get_categories()
        category = categories[0]

        assert isinstance(category.id, int)
        assert isinstance(category.name, str)
        assert isinstance(category.topic_count, int)
        assert isinstance(category.post_count, int)

        if category.slug is not None:
            assert isinstance(category.slug, str)
        if category.description is not None:
            assert isinstance(category.description, str)
        if category.parent_category_id is not None:
            assert isinstance(category.parent_category_id, int)
        if category.color is not None:
            assert isinstance(category.color, str)


class TestAuthModelsFieldTypes:
    """Test auth model field types match expected types."""

    def test_session_field_types(self):
        """Test Session fields have correct types."""
        client = DiscourseClient()
        session = client.get_current_session()

        assert isinstance(session, Session)
        assert isinstance(session.is_authenticated, bool)

        # current_user is None when not authenticated
        assert session.current_user is None

    def test_current_user_field_types(self, authenticated_client):
        """Test CurrentUser fields have correct types."""
        session = authenticated_client.get_current_session()
        user = session.current_user

        assert isinstance(user, CurrentUser)
        assert isinstance(user.id, int)
        assert isinstance(user.username, str)
        assert isinstance(user.unread_notifications, int)
        assert isinstance(user.unread_high_priority_notifications, int)

        if user.name is not None:
            assert isinstance(user.name, str)
        if user.avatar_template is not None:
            assert isinstance(user.avatar_template, str)

    def test_login_result_field_types(self, client, test_username, test_password):
        """Test LoginResult fields have correct types."""
        result = client.login(test_username, test_password)

        assert isinstance(result, LoginResult)
        assert isinstance(result.success, bool)
        assert isinstance(result.requires_2fa, bool)

        if result.username is not None:
            assert isinstance(result.username, str)
        if result.error is not None:
            assert isinstance(result.error, str)


class TestModelDataIntegrity:
    """Test that model data is internally consistent."""

    def test_topic_has_posts(self, client):
        """Test that topic has at least one post."""
        hot = client.get_hot_topics()
        topic_id = hot[0].id

        # Get topic info for post count
        info = client.get_topic_info(topic_id)
        assert info.post_count >= 1, "Topic should have at least 1 post"

        # Get posts
        posts = client.get_topic_posts(topic_id)
        assert len(posts) >= 1, "Should return at least 1 post"

    def test_user_summary_username_matches_request(self, client, test_username):
        """Test user summary username matches requested username."""
        summary = client.get_user_summary(test_username)
        assert summary.username == test_username

    def test_search_post_topic_id_is_valid(self, client):
        """Test search post topic_id references valid topic."""
        result = client.search("credit")

        if len(result.posts) > 0:
            post = result.posts[0]
            # Should be able to get the topic info
            info = client.get_topic_info(post.topic_id)
            assert info.topic_id == post.topic_id
