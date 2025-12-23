"""Authentication API module for login and session management."""

from __future__ import annotations

import logging
import time as _time
from collections.abc import Iterator
from typing import Any

import requests

from uscardforum.api.base import BaseAPI
from uscardforum.models.auth import (
    Bookmark,
    LoginResult,
    Notification,
    NotificationLevel,
    Session,
    SubscriptionResult,
)
from uscardforum.utils.cloudflare import warm_up_session

logger = logging.getLogger(__name__)


class AuthAPI(BaseAPI):
    """API for authentication and session management.

    Handles:
    - Login/logout
    - Session management
    - CSRF tokens
    - Notifications
    - Bookmarks
    - Topic subscriptions
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._csrf_token: str | None = None
        self._logged_in_username: str | None = None

    @property
    def csrf_token(self) -> str | None:
        """Current CSRF token."""
        return self._csrf_token

    @property
    def logged_in_username(self) -> str | None:
        """Currently logged-in username (lazy-loaded for User API Key mode)."""
        if self._logged_in_username:
            return self._logged_in_username

        if "User-Api-Key" in self._session.headers:
            session = self.get_current_session()
            if session.current_user:
                self._logged_in_username = session.current_user.username
                return self._logged_in_username

        return None

    @property
    def is_authenticated(self) -> bool:
        """Whether currently authenticated."""
        if "User-Api-Key" in self._session.headers:
            return True
        return self._logged_in_username is not None

    # -------------------------------------------------------------------------
    # Session Management
    # -------------------------------------------------------------------------

    def warm_up(self, with_delay: bool = True) -> bool:
        """Warm up session to obtain cookies.

        Call this before making authenticated requests to ensure
        Cloudflare cookies are obtained.

        Args:
            with_delay: Add delays between requests for Cloudflare

        Returns:
            True if warm-up was successful (got 200 on at least one URL)
        """
        return warm_up_session(
            self._session,
            self._base_url,
            self._timeout_seconds,
            with_delay=with_delay,
        )

    def fetch_csrf_token(self) -> str:
        """Get CSRF token for authenticated requests.

        Returns:
            CSRF token string

        Raises:
            RuntimeError: If token cannot be obtained
        """
        payload = self._get("/session/csrf.json")
        token: str | None = payload.get("csrf")
        if not token:
            raise RuntimeError("Failed to obtain CSRF token")
        self._csrf_token = token
        self._session.headers["X-CSRF-Token"] = token
        return str(token)

    def get_current_session(self) -> Session:
        """Get current session info.

        Returns:
            Session data including user info (unauthenticated if no session)
        """
        try:
            payload = self._get("/session/current.json")
            return Session.from_api_response(payload)
        except requests.exceptions.HTTPError as e:
            # 404 means no session - return unauthenticated session
            if e.response is not None and e.response.status_code == 404:
                return Session(is_authenticated=False, current_user=None)
            raise

    # -------------------------------------------------------------------------
    # Login
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
        token = self.fetch_csrf_token()

        data: dict[str, Any] = {
            "login": username,
            "password": password,
            "remember": remember_me,
        }
        if second_factor_token:
            data["second_factor_token"] = second_factor_token

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Referer": f"{self._base_url}/login",
            "X-CSRF-Token": token,
            "X-Requested-With": "XMLHttpRequest",
        }

        payload = self._post("/session.json", json=data, headers=headers)
        result = LoginResult.from_api_response(payload, username)

        if result.success:
            # Verify session and get username
            session = self.get_current_session()
            if session.current_user:
                self._logged_in_username = session.current_user.username
            else:
                self._logged_in_username = username

        return result

    def logout(self) -> None:
        """Clear the current session."""
        self._logged_in_username = None
        self._csrf_token = None

    def _require_auth(self) -> None:
        """Raise if not authenticated."""
        if not self.is_authenticated:
            raise RuntimeError(
                "Authentication required. Set NITAN_API_KEY and NITAN_API_CLIENT_ID, or call login(username, password)."
            )

    # -------------------------------------------------------------------------
    # Notifications
    # -------------------------------------------------------------------------

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
        self._require_auth()
        payload = self._get("/notifications.json")
        raw_notifications = payload.get("notifications", [])

        notifications = [Notification(**n) for n in raw_notifications]

        # Apply filters
        if since_id is not None:
            notifications = [n for n in notifications if n.id > since_id]
        if only_unread:
            notifications = [n for n in notifications if not n.read]
        if limit is not None:
            notifications = notifications[: max(0, int(limit))]

        return notifications

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
        self._require_auth()
        current_since = since_id

        if current_since is None:
            existing = self.get_notifications()
            if existing:
                current_since = max(n.id for n in existing)
            else:
                current_since = 0

        while True:
            batch = self.get_notifications(since_id=current_since)
            if batch:
                batch.sort(key=lambda n: n.id)
                for notification in batch:
                    if notification.id > (current_since or 0):
                        current_since = notification.id
                        yield notification
            _time.sleep(poll_interval_seconds)

    # -------------------------------------------------------------------------
    # Bookmarks
    # -------------------------------------------------------------------------

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
            reminder_at: Optional reminder datetime (ISO format)
            auto_delete_preference: Auto-delete setting (default: 3)

        Returns:
            Created bookmark
        """
        self._require_auth()
        token = self._csrf_token or self.fetch_csrf_token()

        form: dict[str, Any] = {
            "bookmarkable_type": "Post",
            "bookmarkable_id": int(post_id),
        }
        if name is not None:
            form["name"] = name
        if reminder_type is not None:
            form["reminder_type"] = str(reminder_type)
        if reminder_at is not None:
            form["reminder_at"] = reminder_at
        if auto_delete_preference is not None:
            form["auto_delete_preference"] = str(int(auto_delete_preference))

        headers = {
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-CSRF-Token": token,
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{self._base_url}/",
        }

        payload = self._post("/bookmarks.json", data=form, headers=headers)
        return Bookmark(
            id=payload.get("id", 0),
            bookmarkable_id=post_id,
            bookmarkable_type="Post",
            name=name,
            reminder_at=None,
            auto_delete_preference=auto_delete_preference or 3,
        )

    # -------------------------------------------------------------------------
    # Subscriptions
    # -------------------------------------------------------------------------

    def subscribe_topic(
        self,
        topic_id: int,
        level: NotificationLevel = NotificationLevel.TRACKING,
    ) -> SubscriptionResult:
        """Set topic notification level (requires auth).

        Args:
            topic_id: Topic ID
            level: Notification level (MUTED, NORMAL, TRACKING, WATCHING)

        Returns:
            Subscription result
        """
        self._require_auth()
        if not isinstance(level, NotificationLevel):
            level = NotificationLevel(level)

        token = self._csrf_token or self.fetch_csrf_token()

        headers = {
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-CSRF-Token": token,
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{self._base_url}/t/{int(topic_id)}",
        }

        self._post(
            f"/t/{int(topic_id)}/notifications",
            data={"notification_level": str(int(level))},
            headers=headers,
        )

        return SubscriptionResult(success=True, notification_level=level)

