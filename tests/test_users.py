"""
Integration tests for Users API.

Tests against the actual USCardForum API with comprehensive field assertions.
"""

import pytest
from datetime import datetime
from uscardforum.models.users import (
    UserSummary,
    UserStats,
    UserAction,
    Badge,
    UserBadges,
    FollowUser,
    FollowList,
    UserReactions,
)


class TestUserSummaryModel:
    """Test UserSummary model fields are populated correctly."""

    def test_user_summary_identity_fields(self, client, test_username):
        """Test UserSummary identity fields."""
        summary = client.get_user_summary(test_username)

        assert isinstance(summary, UserSummary)
        assert summary.username == test_username, "username must match request"
        assert isinstance(summary.username, str)

    def test_user_summary_id_field(self, client, test_username):
        """Test UserSummary user_id field."""
        summary = client.get_user_summary(test_username)

        if summary.user_id is not None:
            assert summary.user_id > 0, "user_id must be positive"

    def test_user_summary_stats_object(self, client, test_username):
        """Test UserSummary has valid stats object."""
        summary = client.get_user_summary(test_username)

        assert summary.stats is not None, "stats should be present"
        assert isinstance(summary.stats, UserStats)

    def test_user_summary_timestamps(self, client, test_username):
        """Test UserSummary timestamp fields."""
        summary = client.get_user_summary(test_username)

        if summary.created_at is not None:
            assert isinstance(summary.created_at, datetime)

        if summary.last_seen_at is not None:
            assert isinstance(summary.last_seen_at, datetime)

    def test_user_summary_lists(self, client, test_username):
        """Test UserSummary list fields."""
        summary = client.get_user_summary(test_username)

        assert isinstance(summary.badges, list), "badges must be list"
        assert isinstance(summary.top_topics, list), "top_topics must be list"
        assert isinstance(summary.top_replies, list), "top_replies must be list"


class TestUserStatsModel:
    """Test UserStats model fields are populated correctly."""

    def test_user_stats_all_counts_non_negative(self, client, test_username):
        """Test all UserStats count fields are non-negative."""
        summary = client.get_user_summary(test_username)
        stats = summary.stats

        assert stats.posts_read_count >= 0, "posts_read_count must be non-negative"
        assert stats.topics_entered >= 0, "topics_entered must be non-negative"
        assert stats.likes_given >= 0, "likes_given must be non-negative"
        assert stats.likes_received >= 0, "likes_received must be non-negative"
        assert stats.days_visited >= 0, "days_visited must be non-negative"
        assert stats.post_count >= 0, "post_count must be non-negative"
        assert stats.topic_count >= 0, "topic_count must be non-negative"

    def test_user_stats_are_integers(self, client, test_username):
        """Test UserStats fields are integers."""
        summary = client.get_user_summary(test_username)
        stats = summary.stats

        assert isinstance(stats.posts_read_count, int)
        assert isinstance(stats.topics_entered, int)
        assert isinstance(stats.likes_given, int)
        assert isinstance(stats.likes_received, int)
        assert isinstance(stats.days_visited, int)
        assert isinstance(stats.post_count, int)
        assert isinstance(stats.topic_count, int)


class TestUserActionModel:
    """Test UserAction model fields are populated correctly."""

    def test_user_actions_returns_list(self, client, test_username):
        """Test get_user_actions returns list of UserAction."""
        actions = client.get_user_actions(test_username)

        assert isinstance(actions, list)

    def test_user_action_fields_when_present(self, client, test_username):
        """Test UserAction fields when user has actions."""
        actions = client.get_user_actions(test_username)

        if len(actions) > 0:
            action = actions[0]
            assert isinstance(action, UserAction)

            # Action type should be present
            if action.action_type is not None:
                assert isinstance(action.action_type, int)

            # Topic reference
            if action.topic_id is not None:
                assert action.topic_id > 0

            if action.post_number is not None:
                assert action.post_number >= 1

    def test_user_replies_are_user_actions(self, client, test_username):
        """Test get_user_replies returns UserAction objects."""
        replies = client.get_user_replies(test_username)

        assert isinstance(replies, list)
        for reply in replies[:5]:
            assert isinstance(reply, UserAction)

    def test_user_topics_are_user_actions(self, client, test_username):
        """Test get_user_topics returns UserAction objects."""
        topics = client.get_user_topics(test_username)

        assert isinstance(topics, list)
        for topic in topics[:5]:
            assert isinstance(topic, UserAction)


class TestBadgeModel:
    """Test Badge model fields are populated correctly."""

    def test_badge_required_fields(self, client, test_username):
        """Test Badge required fields."""
        badges_result = client.get_user_badges(test_username)

        if len(badges_result.badges) > 0:
            badge = badges_result.badges[0]
            assert isinstance(badge, Badge)

            # Required fields
            assert badge.id > 0, "id must be positive"
            assert badge.badge_id > 0, "badge_id must be positive"
            assert badge.name, "name must not be empty"
            assert isinstance(badge.name, str)

    def test_badge_optional_fields(self, client, test_username):
        """Test Badge optional fields when present."""
        badges_result = client.get_user_badges(test_username)

        if len(badges_result.badges) > 0:
            badge = badges_result.badges[0]

            if badge.description is not None:
                assert isinstance(badge.description, str)

            if badge.granted_at is not None:
                assert isinstance(badge.granted_at, datetime)

            if badge.badge_type_id is not None:
                assert isinstance(badge.badge_type_id, int)


class TestUserBadgesModel:
    """Test UserBadges model fields are populated correctly."""

    def test_user_badges_structure(self, client, test_username):
        """Test UserBadges has correct structure."""
        badges = client.get_user_badges(test_username)

        assert isinstance(badges, UserBadges)
        assert isinstance(badges.badges, list), "badges must be list"
        assert isinstance(badges.badge_types, list), "badge_types must be list"

    def test_list_user_badges_returns_strings(self, client, test_username):
        """Test list_user_badges returns list of strings."""
        names = client.list_user_badges(test_username)

        assert isinstance(names, list)
        for name in names:
            assert isinstance(name, str), "badge names must be strings"


class TestFollowListModel:
    """Test FollowList model fields are populated correctly."""

    def test_following_list_structure(self, client, test_username):
        """Test get_user_following returns valid FollowList."""
        following = client.get_user_following(test_username)

        assert isinstance(following, FollowList)
        assert isinstance(following.users, list), "users must be list"
        assert isinstance(following.total_count, int), "total_count must be int"
        assert following.total_count >= 0, "total_count must be non-negative"

    def test_followers_list_structure(self, client, test_username):
        """Test get_user_followers returns valid FollowList."""
        followers = client.get_user_followers(test_username)

        assert isinstance(followers, FollowList)
        assert isinstance(followers.users, list)
        assert followers.total_count >= 0

    def test_follow_user_fields(self, client, test_username):
        """Test FollowUser fields when present."""
        following = client.get_user_following(test_username)

        if len(following.users) > 0:
            user = following.users[0]
            assert isinstance(user, FollowUser)

            # Required fields
            assert user.id > 0, "id must be positive"
            assert user.username, "username must not be empty"
            assert isinstance(user.username, str)


class TestUserReactionsModel:
    """Test UserReactions model fields are populated correctly."""

    def test_user_reactions_structure(self, client, test_username):
        """Test get_user_reactions returns valid UserReactions."""
        reactions = client.get_user_reactions(test_username)

        assert isinstance(reactions, UserReactions)
        assert isinstance(reactions.reactions, list), "reactions must be list"

    def test_user_reactions_returns_list_of_reactions(self, client, test_username):
        """Test reactions field contains reaction data."""
        reactions = client.get_user_reactions(test_username)

        # User may or may not have reactions
        for reaction in reactions.reactions:
            # Each reaction should be a dict or object
            assert reaction is not None


class TestSystemUser:
    """Test with system user for predictable results."""

    def test_system_user_has_stats(self, client):
        """Test system user has meaningful stats."""
        summary = client.get_user_summary("system")

        assert isinstance(summary, UserSummary)
        assert summary.username == "system"
        assert summary.stats is not None
