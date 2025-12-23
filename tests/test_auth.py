"""
Integration tests for Authentication API.

Tests against the actual USCardForum API with comprehensive field assertions.
"""

import pytest
from datetime import datetime
from uscardforum.client import DiscourseClient
from uscardforum.models.auth import (
    LoginResult,
    Session,
    CurrentUser,
    Notification,
    Bookmark,
    SubscriptionResult,
    NotificationLevel,
)


class TestLoginResultModel:
    """Test LoginResult model fields are populated correctly."""

    def test_login_success_fields(self, client, test_username, test_password):
        """Test LoginResult fields on successful login."""
        result = client.login(test_username, test_password)

        assert isinstance(result, LoginResult)
        assert result.success is True, "Login should succeed"
        assert result.username == test_username, "username should match"
        assert result.error is None, "error should be None on success"
        assert result.requires_2fa is False, "requires_2fa should be False"

    def test_login_failure_fields(self, client):
        """Test LoginResult fields on failed login."""
        result = client.login("nonexistent_user_xyz123", "wrongpassword")

        assert isinstance(result, LoginResult)
        assert result.success is False, "Login should fail"
        assert result.error is not None, "error should be present on failure"
        assert isinstance(result.error, str)

    def test_login_result_boolean_fields(self, client, test_username, test_password):
        """Test LoginResult boolean fields are actual booleans."""
        result = client.login(test_username, test_password)

        assert isinstance(result.success, bool)
        assert isinstance(result.requires_2fa, bool)


class TestSessionModel:
    """Test Session model fields are populated correctly."""

    def test_session_unauthenticated_fields(self):
        """Test Session fields when not authenticated."""
        fresh_client = DiscourseClient()
        session = fresh_client.get_current_session()

        assert isinstance(session, Session)
        assert session.is_authenticated is False, "Should not be authenticated"
        assert session.current_user is None, "current_user should be None"

        # Session JSON should only contain Session model fields
        session_keys = set(session.model_dump().keys())
        model_keys = set(Session.model_fields.keys())
        assert session_keys.issubset(model_keys)

    def test_session_authenticated_fields(self, authenticated_client):
        """Test Session fields when authenticated."""
        session = authenticated_client.get_current_session()

        assert isinstance(session, Session)
        assert session.is_authenticated is True, "Should be authenticated"
        assert session.current_user is not None, "current_user should be present"

        session_keys = set(session.model_dump().keys())
        model_keys = set(Session.model_fields.keys())
        assert session_keys.issubset(model_keys)

    def test_session_is_authenticated_is_boolean(self, authenticated_client):
        """Test is_authenticated is actual boolean."""
        session = authenticated_client.get_current_session()

        assert isinstance(session.is_authenticated, bool)


class TestUserApiKeyAuth:
    """Test User API Key authentication mode."""

    def test_is_authenticated_with_user_api_key(self, client):
        """Test is_authenticated returns True when User-Api-Key header is set."""
        client._session.headers["User-Api-Key"] = "test_api_key"

        assert client.is_authenticated is True

    def test_is_authenticated_with_logged_in_username(self, client):
        """Test is_authenticated returns True when _logged_in_username is set."""
        client._logged_in_username = "test_user"

        assert client.is_authenticated is True


class TestCurrentUserModel:
    """Test CurrentUser model fields are populated correctly."""

    def test_current_user_required_fields(self, authenticated_client):
        """Test CurrentUser required fields."""
        session = authenticated_client.get_current_session()
        user = session.current_user

        assert isinstance(user, CurrentUser)
        assert user.id > 0, "id must be positive"
        assert user.username, "username must not be empty"
        assert isinstance(user.username, str)

        # Ensure JSON output stays within CurrentUser domain fields
        user_keys = set(user.model_dump().keys())
        model_keys = set(CurrentUser.model_fields.keys())
        assert user_keys.issubset(model_keys)

    def test_current_user_notification_counts(self, authenticated_client):
        """Test CurrentUser notification count fields."""
        session = authenticated_client.get_current_session()
        user = session.current_user

        assert user.unread_notifications >= 0, "unread_notifications must be non-negative"
        assert user.unread_high_priority_notifications >= 0, "high_priority must be non-negative"
        assert isinstance(user.unread_notifications, int)
        assert isinstance(user.unread_high_priority_notifications, int)

    def test_current_user_optional_fields(self, authenticated_client):
        """Test CurrentUser optional fields."""
        session = authenticated_client.get_current_session()
        user = session.current_user

        if user.name is not None:
            assert isinstance(user.name, str)

        if user.avatar_template is not None:
            assert isinstance(user.avatar_template, str)


class TestNotificationModel:
    """Test Notification model fields are populated correctly."""

    def test_notifications_returns_list(self, authenticated_client):
        """Test get_notifications returns list."""
        notifications = authenticated_client.get_notifications()

        assert isinstance(notifications, list)

    def test_notification_required_fields(self, authenticated_client):
        """Test Notification required fields when present."""
        notifications = authenticated_client.get_notifications()

        if len(notifications) > 0:
            notif = notifications[0]
            assert isinstance(notif, Notification)

            assert notif.id > 0, "id must be positive"
            assert isinstance(notif.notification_type, int)
            assert notif.notification_type >= 0

    def test_notification_read_is_boolean(self, authenticated_client):
        """Test Notification read field is boolean."""
        notifications = authenticated_client.get_notifications()

        if len(notifications) > 0:
            notif = notifications[0]
            assert isinstance(notif.read, bool)

    def test_notification_optional_fields(self, authenticated_client):
        """Test Notification optional fields."""
        notifications = authenticated_client.get_notifications()

        if len(notifications) > 0:
            notif = notifications[0]

            if notif.created_at is not None:
                assert isinstance(notif.created_at, datetime)

            if notif.topic_id is not None:
                assert notif.topic_id > 0

            if notif.post_number is not None:
                assert notif.post_number >= 1

            if notif.slug is not None:
                assert isinstance(notif.slug, str)

            assert isinstance(notif.data, dict)


class TestBookmarkModel:
    """Test Bookmark model fields are populated correctly."""

    def test_bookmark_post_returns_bookmark(self, authenticated_client):
        """Test bookmark_post returns Bookmark object."""
        # Get a post to bookmark
        hot_topics = authenticated_client.get_hot_topics()
        posts = authenticated_client.get_topic_posts(hot_topics[0].id)
        post_id = posts[0].id

        result = authenticated_client.bookmark_post(post_id)

        assert isinstance(result, Bookmark)

    def test_bookmark_fields(self, authenticated_client):
        """Test Bookmark fields are valid."""
        hot_topics = authenticated_client.get_hot_topics()
        posts = authenticated_client.get_topic_posts(hot_topics[0].id)
        post_id = posts[0].id

        bookmark = authenticated_client.bookmark_post(post_id)

        assert bookmark.id > 0, "id must be positive"
        assert bookmark.bookmarkable_id > 0, "bookmarkable_id must be positive"
        assert bookmark.bookmarkable_type, "bookmarkable_type must be present"
        assert isinstance(bookmark.bookmarkable_type, str)

        bookmark_keys = set(bookmark.model_dump().keys())
        model_keys = set(Bookmark.model_fields.keys())
        assert bookmark_keys.issubset(model_keys)

    def test_bookmark_optional_fields(self, authenticated_client):
        """Test Bookmark optional fields."""
        hot_topics = authenticated_client.get_hot_topics()
        posts = authenticated_client.get_topic_posts(hot_topics[0].id)
        post_id = posts[0].id

        bookmark = authenticated_client.bookmark_post(post_id)

        if bookmark.name is not None:
            assert isinstance(bookmark.name, str)

        if bookmark.reminder_at is not None:
            assert isinstance(bookmark.reminder_at, datetime)

        assert isinstance(bookmark.auto_delete_preference, int)


class TestSubscriptionResultModel:
    """Test SubscriptionResult model fields are populated correctly."""

    def test_subscribe_topic_returns_result(self, authenticated_client):
        """Test subscribe_topic returns SubscriptionResult."""
        hot_topics = authenticated_client.get_hot_topics()
        topic_id = hot_topics[0].id

        result = authenticated_client.subscribe_topic(topic_id, level=3)

        assert isinstance(result, SubscriptionResult)

    def test_subscription_result_fields(self, authenticated_client):
        """Test SubscriptionResult fields."""
        hot_topics = authenticated_client.get_hot_topics()
        topic_id = hot_topics[0].id

        result = authenticated_client.subscribe_topic(topic_id, level=2)

        assert isinstance(result.success, bool)
        assert result.success is True

        # notification_level should be valid
        assert isinstance(result.notification_level, NotificationLevel)

        result_keys = set(result.model_dump().keys())
        model_keys = set(SubscriptionResult.model_fields.keys())
        assert result_keys.issubset(model_keys)

    def test_subscription_levels(self, authenticated_client):
        """Test different subscription levels."""
        hot_topics = authenticated_client.get_hot_topics()
        topic_id = hot_topics[0].id

        # Test different levels
        for level in [1, 2, 3]:
            result = authenticated_client.subscribe_topic(topic_id, level=level)
            assert result.success is True
