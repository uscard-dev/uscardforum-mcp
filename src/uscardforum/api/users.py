"""Users API module for user profiles and activity."""

from __future__ import annotations

from typing import Any

from uscardforum.api.base import BaseAPI
from uscardforum.models.users import (
    Badge,
    FollowList,
    FollowUser,
    UserAction,
    UserBadges,
    UserReactions,
    UserStats,
    UserSummary,
)


class UsersAPI(BaseAPI):
    """API for user profile and activity operations.

    Handles:
    - User profile summaries
    - User activity and actions
    - Badges
    - Social connections (followers/following)
    """

    # -------------------------------------------------------------------------
    # User Profile
    # -------------------------------------------------------------------------

    def get_user_summary(self, username: str) -> UserSummary:
        """Fetch user profile summary.

        Args:
            username: User handle

        Returns:
            Comprehensive user summary
        """
        payload = self._get(f"/u/{username}/summary.json")

        # Extract user stats from various locations
        user_summary = payload.get("user_summary", {})
        user = payload.get("users", [{}])[0] if payload.get("users") else {}

        stats = UserStats(
            likes_given=user_summary.get("likes_given", 0),
            likes_received=user_summary.get("likes_received", 0),
            days_visited=user_summary.get("days_visited", 0),
            post_count=user_summary.get("post_count", 0),
            topic_count=user_summary.get("topic_count", 0),
            posts_read_count=user_summary.get("posts_read_count", 0),
            topics_entered=user_summary.get("topics_entered", 0),
        )

        badges = []
        for b in user_summary.get("badges", []):
            badges.append(Badge(
                id=b.get("id", 0),
                badge_id=b.get("badge_id", b.get("id", 0)),
                name=b.get("name", ""),
                description=b.get("description"),
                granted_at=b.get("granted_at"),
                badge_type_id=b.get("badge_type_id"),
            ))

        return UserSummary(
            user_id=user.get("id"),
            username=user.get("username", username),
            name=user.get("name"),
            created_at=user.get("created_at"),
            last_seen_at=user.get("last_seen_at"),
            stats=stats,
            badges=badges,
            top_topics=user_summary.get("top_topics", []),
            top_replies=user_summary.get("top_replies", []),
        )

    # -------------------------------------------------------------------------
    # User Activity
    # -------------------------------------------------------------------------

    def get_user_actions(
        self,
        username: str,
        *,
        filter: int | None = None,
        offset: int | None = None,
    ) -> list[UserAction]:
        """Fetch user actions/activity.

        Args:
            username: User handle
            filter: Optional action filter (e.g., 5 for replies)
            offset: Optional pagination offset

        Returns:
            List of user action objects
        """
        params_list: list[tuple[str, Any]] = [("username", username)]
        if filter is not None:
            params_list.append(("filter", int(filter)))
        if offset is not None:
            params_list.append(("offset", int(offset)))

        payload = self._get("/user_actions.json", params=params_list)
        actions = payload.get("user_actions", [])
        return [UserAction(**a) for a in actions]

    def get_user_replies(
        self,
        username: str,
        offset: int | None = None,
    ) -> list[UserAction]:
        """Fetch user's replies.

        Args:
            username: User handle
            offset: Optional pagination offset

        Returns:
            List of reply action objects
        """
        return self.get_user_actions(username, filter=5, offset=offset)

    def get_user_topics(
        self,
        username: str,
        page: int | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch topics created by user.

        Args:
            username: User handle
            page: Optional page number

        Returns:
            List of topic objects (raw API format)
        """
        params_list: list[tuple[str, Any]] = []
        if page is not None:
            params_list.append(("page", int(page)))

        payload = self._get(
            f"/topics/created-by/{username}.json",
            params=params_list,
        )
        topics: list[dict[str, Any]] = payload.get("topic_list", {}).get("topics", [])
        return topics

    # -------------------------------------------------------------------------
    # Badges
    # -------------------------------------------------------------------------

    def get_user_badges(
        self,
        username: str,
        grouped: bool = True,
    ) -> UserBadges:
        """Fetch user's badges.

        Args:
            username: User handle
            grouped: Group badges (default: True)

        Returns:
            User badges data
        """
        params_list: list[tuple[str, Any]] = [
            ("grouped", str(bool(grouped)).lower())
        ]
        payload = self._get(f"/user-badges/{username}.json", params=params_list)

        badges = []
        for b in payload.get("user_badges", []):
            badges.append(Badge(
                id=b.get("id", 0),
                badge_id=b.get("badge_id", 0),
                name=b.get("name", ""),
                description=b.get("description"),
                granted_at=b.get("granted_at"),
                badge_type_id=b.get("badge_type_id"),
            ))

        return UserBadges(badges=badges)

    def list_users_with_badge(
        self,
        badge_id: int,
        offset: int | None = None,
    ) -> dict[str, Any]:
        """List users with a specific badge.

        Args:
            badge_id: Badge ID
            offset: Optional pagination offset

        Returns:
            Raw API response with users
        """
        params_list: list[tuple[str, Any]] = [("badge_id", int(badge_id))]
        if offset is not None:
            params_list.append(("offset", int(offset)))

        return self._get("/user_badges.json", params=params_list)

    # -------------------------------------------------------------------------
    # Social
    # -------------------------------------------------------------------------

    def get_user_following(
        self,
        username: str,
        page: int | None = None,
    ) -> FollowList:
        """Fetch users that a user follows.

        Args:
            username: User handle
            page: Optional page number

        Returns:
            List of followed users
        """
        params_list: list[tuple[str, Any]] = []
        if page is not None:
            params_list.append(("page", int(page)))

        payload = self._get(
            f"/u/{username}/follow/following.json",
            params=params_list,
        )

        users = []
        for u in payload.get("users", []):
            users.append(FollowUser(
                id=u.get("id", 0),
                username=u.get("username", ""),
                name=u.get("name"),
                avatar_template=u.get("avatar_template"),
            ))

        return FollowList(
            users=users,
            total_count=payload.get("total_count", len(users)),
        )

    def get_user_followers(
        self,
        username: str,
        page: int | None = None,
    ) -> FollowList:
        """Fetch users following a user.

        Args:
            username: User handle
            page: Optional page number

        Returns:
            List of follower users
        """
        params_list: list[tuple[str, Any]] = []
        if page is not None:
            params_list.append(("page", int(page)))

        payload = self._get(
            f"/u/{username}/follow/followers.json",
            params=params_list,
        )

        users = []
        for u in payload.get("users", []):
            users.append(FollowUser(
                id=u.get("id", 0),
                username=u.get("username", ""),
                name=u.get("name"),
                avatar_template=u.get("avatar_template"),
            ))

        return FollowList(
            users=users,
            total_count=payload.get("total_count", len(users)),
        )

    def get_user_reactions(
        self,
        username: str,
        offset: int | None = None,
    ) -> UserReactions:
        """Fetch user's post reactions.

        Args:
            username: User handle
            offset: Optional pagination offset

        Returns:
            User reactions data
        """
        params_list: list[tuple[str, Any]] = [("username", username)]
        if offset is not None:
            params_list.append(("offset", int(offset)))

        payload = self._get(
            "/discourse-reactions/posts/reactions.json",
            params=params_list,
        )
        return UserReactions(reactions=payload.get("reactions", []))

