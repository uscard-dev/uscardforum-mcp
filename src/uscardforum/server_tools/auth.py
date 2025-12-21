"""MCP tools for authentication and subscriptions."""
from __future__ import annotations

from uscardforum.models.auth import (
    Bookmark,
    LoginResult,
    Notification,
    Session,
    SubscriptionResult,
)
from uscardforum.server_core import get_client, mcp


@mcp.tool()
def login(
    username: str,
    password: str,
    second_factor_token: str | None = None,
) -> LoginResult:
    """
    Authenticate with USCardForum credentials.

    Args:
        username: Your forum username
        password: Your forum password
        second_factor_token: 2FA code if you have 2FA enabled (optional)

    IMPORTANT: Only use this if you need authenticated features like:
    - Reading notifications
    - Bookmarking posts
    - Subscribing to topics

    Most read operations work without authentication.

    Returns a LoginResult with:
    - success: Whether login succeeded
    - username: Logged-in username
    - error: Error message if failed
    - requires_2fa: Whether 2FA is required

    The session remains authenticated for subsequent calls.

    Security note: Credentials are used only for this session
    and are not persisted.
    """
    return get_client().login(
        username, password, second_factor_token=second_factor_token
    )


@mcp.tool()
def get_current_session() -> Session:
    """
    Get information about the current session.

    Returns a Session object with:
    - is_authenticated: Whether logged in
    - current_user: CurrentUser object with user info (if authenticated)

    Use to verify authentication status.
    """
    return get_client().get_current_session()


@mcp.tool()
def get_notifications(
    since_id: int | None = None,
    only_unread: bool = False,
    limit: int | None = None,
) -> list[Notification]:
    """
    Fetch your notifications. REQUIRES AUTHENTICATION.

    Args:
        since_id: Only get notifications newer than this ID (optional)
        only_unread: Only return unread notifications (default: False)
        limit: Maximum number to return (optional)

    Must call login() first.

    Returns a list of Notification objects with:
    - id: Notification ID
    - notification_type: Type of notification
    - read: Whether read
    - topic_id: Related topic
    - post_number: Related post
    - created_at: When created

    Use to:
    - Check for new replies to your posts
    - See mentions and likes
    - Track topic updates you're watching
    """
    return get_client().get_notifications(
        since_id=since_id, only_unread=only_unread, limit=limit
    )


@mcp.tool()
def bookmark_post(
    post_id: int,
    name: str | None = None,
    reminder_type: int | None = None,
    reminder_at: str | None = None,
    auto_delete_preference: int | None = 3,
) -> Bookmark:
    """
    Bookmark a post for later reference. REQUIRES AUTHENTICATION.

    Args:
        post_id: The numeric post ID to bookmark
        name: Optional label/name for the bookmark
        reminder_type: Optional reminder setting
        reminder_at: Optional reminder datetime (ISO format)
        auto_delete_preference: When to auto-delete (default: 3)
            - 0: Never
            - 1: When reminder sent
            - 2: On click
            - 3: Clear after 3 days

    Must call login() first.

    Returns a Bookmark object with the created bookmark information.

    Use to save interesting posts for later reference.
    """
    return get_client().bookmark_post(
        post_id,
        name=name,
        reminder_type=reminder_type,
        reminder_at=reminder_at,
        auto_delete_preference=auto_delete_preference,
    )


@mcp.tool()
def subscribe_topic(
    topic_id: int,
    level: int = 2,
) -> SubscriptionResult:
    """
    Set your notification level for a topic. REQUIRES AUTHENTICATION.

    Args:
        topic_id: The topic ID to subscribe to
        level: Notification level:
            - 0: Muted (no notifications)
            - 1: Normal (only if mentioned)
            - 2: Tracking (notify on replies to your posts)
            - 3: Watching (notify on all new posts)

    Must call login() first.

    Returns a SubscriptionResult with:
    - success: Whether subscription succeeded
    - notification_level: The new notification level

    Use to:
    - Watch topics for all updates (level=3)
    - Mute noisy topics (level=0)
    - Track topics you've contributed to (level=2)
    """
    return get_client().subscribe_topic(topic_id, level=level)


__all__ = [
    "login",
    "get_current_session",
    "get_notifications",
    "bookmark_post",
    "subscribe_topic",
]

