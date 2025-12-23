"""Main Discourse client for USCardForum.

This module provides the primary interface for interacting with the forum,
composing all API modules into a unified client.
"""
from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import requests

from uscardforum.api.auth import AuthAPI
from uscardforum.api.categories import CategoriesAPI
from uscardforum.api.search import SearchAPI
from uscardforum.api.topics import TopicsAPI
from uscardforum.api.users import UsersAPI
from uscardforum.models.auth import (
    Bookmark,
    LoginResult,
    Notification,
    NotificationLevel,
    Session,
    SubscriptionResult,
)
from uscardforum.models.categories import CategoryMap
from uscardforum.models.search import SearchResult
from uscardforum.models.topics import (
    CreatedPost,
    CreatedTopic,
    Post,
    TopicInfo,
    TopicSummary,
)
from uscardforum.models.users import (
    FollowList,
    UserAction,
    UserBadges,
    UserReactions,
    UserSummary,
)
from uscardforum.utils.cloudflare import (
    create_cloudflare_session_with_fallback,
    extended_warm_up,
)

DEFAULT_BASE_URL: str = "https://www.uscardforum.com"


class DiscourseClient:
    """Client for interacting with USCardForum Discourse API.

    This client provides a unified interface for:
    - Browsing topics and posts
    - Searching the forum
    - Viewing user profiles and activity
    - Authentication and session management
    - Bookmarking and subscribing (when authenticated)

    The client handles Cloudflare protection via cloudscraper and implements
    rate limiting to respect server resources.

    Example:
        ```python
        client = DiscourseClient()

        # Browse hot topics
        topics = client.get_hot_topics()
        for topic in topics:
            print(f"{topic.title} ({topic.posts_count} posts)")

        # Read a topic
        info = client.get_topic_info(12345)
        posts = client.get_topic_posts(12345)

        # Search
        results = client.search("Chase Sapphire")
        ```
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout_seconds: float = 15.0,
        session: requests.Session | None = None,
        user_api_key: str | None = None,
        user_api_client_id: str | None = None,
    ) -> None:
        """Initialize the Discourse client.

        Args:
            base_url: Forum base URL (default: https://www.uscardforum.com)
            timeout_seconds: Default request timeout (default: 15.0)
            session: Optional custom requests Session
            user_api_key: Optional User API Key for authentication
            user_api_client_id: Optional User API Client ID for authentication
        """
        normalized = base_url.rstrip("/")
        self._base_url = normalized
        self._timeout_seconds = timeout_seconds

        # Create session with Cloudflare bypass
        if session is not None:
            self._session = session
        else:
            self._session = create_cloudflare_session_with_fallback(
                normalized, timeout_seconds
            )

        if user_api_key and user_api_client_id:
            self._session.headers.update(
                {"User-Api-Key": user_api_key, "User-Api-Client-Id": user_api_client_id}
            )

        # Initialize API modules
        self._topics = TopicsAPI(self._session, normalized, timeout_seconds)
        self._users = UsersAPI(self._session, normalized, timeout_seconds)
        self._search = SearchAPI(self._session, normalized, timeout_seconds)
        self._categories = CategoriesAPI(self._session, normalized, timeout_seconds)
        self._auth = AuthAPI(self._session, normalized, timeout_seconds)

        # Warm up session with extended strategy
        extended_warm_up(self._session, normalized, timeout_seconds)

    def _enrich_with_categories(self, objects: list[Any]) -> list[Any]:
        """Enrich objects with category names using cached map.

        Supports objects with category_id/category_name attributes (like TopicSummary)
        and dictionaries with category_id key.

        Args:
            objects: List of objects to enrich

        Returns:
            Enriched objects
        """
        try:
            category_map = self.get_category_map().categories
            for obj in objects:
                # Handle Pydantic models (TopicSummary, SearchTopic)
                if hasattr(obj, "category_id") and hasattr(obj, "category_name"):
                    if obj.category_id and obj.category_id in category_map:
                        obj.category_name = category_map[obj.category_id]
                # Handle dictionaries
                elif isinstance(obj, dict):
                    cat_id = obj.get("category_id")
                    if cat_id and cat_id in category_map:
                        obj["category_name"] = category_map[cat_id]
        except Exception:
            # Fail gracefully if category map cannot be fetched
            pass
        return objects

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def base_url(self) -> str:
        """Forum base URL."""
        return self._base_url

    @property
    def is_authenticated(self) -> bool:
        """Whether currently logged in."""
        return self._auth.is_authenticated

    @property
    def logged_in_username(self) -> str | None:
        """Currently logged-in username."""
        return self._auth.logged_in_username

    # -------------------------------------------------------------------------
    # Topic Methods
    # -------------------------------------------------------------------------

    def get_hot_topics(self, *, page: int | None = None) -> list[TopicSummary]:
        """Fetch currently hot/trending topics.

        Args:
            page: Page number for pagination (0-indexed, default: 0)

        Returns:
            List of hot topic summaries
        """
        topics = self._topics.get_hot_topics(page=page)
        return self._enrich_with_categories(topics)

    def get_new_topics(self, *, page: int | None = None) -> list[TopicSummary]:
        """Fetch latest new topics.

        Args:
            page: Page number for pagination (0-indexed, default: 0)

        Returns:
            List of new topic summaries
        """
        topics = self._topics.get_new_topics(page=page)
        return self._enrich_with_categories(topics)

    def get_top_topics(
        self, period: str = "monthly", *, page: int | None = None
    ) -> list[TopicSummary]:
        """Fetch top topics for a time period.

        Args:
            period: One of 'daily', 'weekly', 'monthly', 'quarterly', 'yearly'
            page: Page number for pagination (0-indexed, default: 0)

        Returns:
            List of top topic summaries
        """
        topics = self._topics.get_top_topics(period=period, page=page)
        return self._enrich_with_categories(topics)

    def get_topic_info(self, topic_id: int) -> TopicInfo:
        """Fetch topic metadata.

        Args:
            topic_id: Topic ID

        Returns:
            Topic info with post count, title, timestamps
        """
        return self._topics.get_topic_info(topic_id)

    def get_topic_posts(
        self,
        topic_id: int,
        *,
        post_number: int = 1,
        include_raw: bool = False,
    ) -> list[Post]:
        """Fetch a batch of posts starting at a specific post number.

        Args:
            topic_id: Topic ID
            post_number: Starting post number (default: 1)
            include_raw: Include raw markdown (default: False)

        Returns:
            List of posts sorted by post_number
        """
        return self._topics.get_topic_posts(
            topic_id, post_number=post_number, include_raw=include_raw
        )

    def get_all_topic_posts(
        self,
        topic_id: int,
        *,
        include_raw: bool = False,
        start_post_number: int = 1,
        end_post_number: int | None = None,
        max_posts: int | None = None,
    ) -> list[Post]:
        """Fetch all posts in a topic with automatic pagination.

        Args:
            topic_id: Topic ID
            include_raw: Include raw markdown (default: False)
            start_post_number: Starting post number (default: 1)
            end_post_number: Optional ending post number
            max_posts: Optional maximum posts to fetch

        Returns:
            List of all matching posts
        """
        return self._topics.get_all_topic_posts(
            topic_id,
            include_raw=include_raw,
            start_post_number=start_post_number,
            end_post_number=end_post_number,
            max_posts=max_posts,
        )

    # -------------------------------------------------------------------------
    # Search Methods
    # -------------------------------------------------------------------------

    def search(
        self,
        query: str,
        *,
        page: int | None = None,
        order: str | None = None,
    ) -> SearchResult:
        """Search the forum.

        Args:
            query: Search query (supports Discourse operators)
            page: Optional page number
            order: Optional sort order

        Returns:
            Search results with posts, topics, and users
        """
        result = self._search.search(query, page=page, order=order)
        self._enrich_with_categories(result.topics)
        return result

    # -------------------------------------------------------------------------
    # Category Methods
    # -------------------------------------------------------------------------

    def get_categories(self) -> list:
        """Fetch all forum categories.

        Returns:
            List of Category objects (including subcategories)
        """
        return self._categories.get_categories()

    def get_category_map(self) -> CategoryMap:
        """Get mapping of category IDs to names.

        Returns:
            CategoryMap with ID to name mapping
        """
        return self._categories.get_category_map()

    # -------------------------------------------------------------------------
    # User Methods
    # -------------------------------------------------------------------------

    def get_user_summary(self, username: str) -> UserSummary:
        """Fetch user profile summary.

        Args:
            username: User handle

        Returns:
            Comprehensive user summary
        """
        summary = self._users.get_user_summary(username)
        if summary.top_topics:
            self._enrich_with_categories(summary.top_topics)
        return summary

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
        return self._users.get_user_actions(username, filter=filter, offset=offset)

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
        return self._users.get_user_replies(username, offset=offset)

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
            List of topic objects
        """
        topics = self._users.get_user_topics(username, page=page)
        return self._enrich_with_categories(topics)

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
        return self._users.get_user_badges(username, grouped=grouped)

    def list_user_badges(
        self,
        badge_id: int,
        offset: int | None = None,
    ) -> dict[str, Any]:
        """List users with a specific badge.

        Args:
            badge_id: Badge ID
            offset: Optional pagination offset

        Returns:
            Users with the badge
        """
        return self._users.list_users_with_badge(badge_id, offset=offset)

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
        return self._users.get_user_following(username, page=page)

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
        return self._users.get_user_followers(username, page=page)

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
        return self._users.get_user_reactions(username, offset=offset)

    # -------------------------------------------------------------------------
    # Authentication Methods
    # -------------------------------------------------------------------------

    def login(
        self,
        username: str,
        password: str,
        second_factor_token: str | None = None,
        remember_me: bool = True,
    ) -> LoginResult:
        """Login to the forum.

        Args:
            username: Forum username
            password: Forum password
            second_factor_token: Optional 2FA token
            remember_me: Remember session (default: True)

        Returns:
            Login result with success status
        """
        return self._auth.login(
            username, password, second_factor_token=second_factor_token, remember_me=remember_me
        )

    def get_current_session(self) -> Session:
        """Get current session info.

        Returns:
            Session data including user info
        """
        return self._auth.get_current_session()

    def get_notifications(
        self,
        since_id: int | None = None,
        only_unread: bool = False,
        limit: int | None = None,
    ) -> list[Notification]:
        """Fetch notifications (requires auth).

        Args:
            since_id: Only notifications after this ID
            only_unread: Only unread notifications
            limit: Maximum notifications to return

        Returns:
            List of notification objects
        """
        return self._auth.get_notifications(
            since_id=since_id, only_unread=only_unread, limit=limit
        )

    def iter_notifications(
        self,
        poll_interval_seconds: float = 10.0,
        since_id: int | None = None,
    ) -> Iterator[Notification]:
        """Yield new notifications by polling.

        Args:
            poll_interval_seconds: Poll interval (default: 10.0)
            since_id: Start from this notification ID

        Yields:
            New notification objects
        """
        yield from self._auth.iter_notifications(
            poll_interval_seconds=poll_interval_seconds, since_id=since_id
        )

    def bookmark_post(
        self,
        post_id: int,
        name: str | None = None,
        reminder_type: int | None = None,
        reminder_at: str | None = None,
        auto_delete_preference: int | None = 3,
    ) -> Bookmark:
        """Bookmark a post (requires auth).

        Args:
            post_id: Post ID to bookmark
            name: Optional bookmark name
            reminder_type: Optional reminder type
            reminder_at: Optional reminder datetime
            auto_delete_preference: Auto-delete setting (default: 3)

        Returns:
            Created bookmark
        """
        return self._auth.bookmark_post(
            post_id,
            name=name,
            reminder_type=reminder_type,
            reminder_at=reminder_at,
            auto_delete_preference=auto_delete_preference,
        )

    def subscribe_topic(
        self,
        topic_id: int,
        level: int = 2,
    ) -> SubscriptionResult:
        """Set topic notification level (requires auth).

        Args:
            topic_id: Topic ID
            level: 0=muted, 1=normal, 2=tracking, 3=watching

        Returns:
            Subscription result
        """
        return self._auth.subscribe_topic(topic_id, level=NotificationLevel(level))

    # -------------------------------------------------------------------------
    # Write Methods (create topics/posts)
    # -------------------------------------------------------------------------

    def create_topic(
        self,
        title: str,
        raw: str,
        category_id: int | None = None,
        tags: list[str] | None = None,
    ) -> CreatedTopic:
        """Create a new topic (requires auth).

        Args:
            title: Topic title
            raw: Post content in markdown
            category_id: Optional category ID
            tags: Optional list of tags

        Returns:
            Created topic info with topic_id, slug, and post_id
        """
        self._auth._require_auth()
        csrf_token = self._auth._csrf_token or self._auth.fetch_csrf_token()
        return self._topics.create_topic(
            title=title,
            raw=raw,
            category_id=category_id,
            tags=tags,
            csrf_token=csrf_token,
        )

    def create_post(
        self,
        topic_id: int,
        raw: str,
        reply_to_post_number: int | None = None,
    ) -> CreatedPost:
        """Create a new post/reply in an existing topic (requires auth).

        Args:
            topic_id: Topic ID to reply to
            raw: Post content in markdown
            reply_to_post_number: Optional post number to reply to

        Returns:
            Created post info with post_id, post_number, etc.
        """
        self._auth._require_auth()
        csrf_token = self._auth._csrf_token or self._auth.fetch_csrf_token()
        return self._topics.create_post(
            topic_id=topic_id,
            raw=raw,
            reply_to_post_number=reply_to_post_number,
            csrf_token=csrf_token,
        )
