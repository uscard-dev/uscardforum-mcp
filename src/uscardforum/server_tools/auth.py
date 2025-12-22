"""MCP tools for authentication and subscriptions."""
from __future__ import annotations

from typing import Annotated

from pydantic import Field

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
    username: Annotated[
        str,
        Field(description="Your forum username"),
    ],
    password: Annotated[
        str,
        Field(description="Your forum password"),
    ],
    second_factor_token: Annotated[
        str | None,
        Field(default=None, description="2FA code if you have 2FA enabled"),
    ] = None,
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
    since_id: Annotated[
        int | None,
        Field(default=None, description="Only get notifications newer than this ID"),
    ] = None,
    only_unread: Annotated[
        bool,
        Field(default=False, description="Only return unread notifications"),
    ] = False,
    limit: Annotated[
        int | None,
        Field(default=None, description="Maximum number to return"),
    ] = None,
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
    post_id: Annotated[
        int,
        Field(description="The numeric post ID to bookmark"),
    ],
    name: Annotated[
        str | None,
        Field(default=None, description="Label/name for the bookmark"),
    ] = None,
    reminder_type: Annotated[
        int | None,
        Field(default=None, description="Reminder setting"),
    ] = None,
    reminder_at: Annotated[
        str | None,
        Field(default=None, description="Reminder datetime (ISO format)"),
    ] = None,
    auto_delete_preference: Annotated[
        int | None,
        Field(
            default=3,
            description="When to auto-delete: 0=never, 1=when reminder sent, 2=on click, 3=after 3 days (default)",
        ),
    ] = 3,
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
    topic_id: Annotated[
        int,
        Field(description="The topic ID to subscribe to"),
    ],
    level: Annotated[
        int,
        Field(
            default=2,
            description="Notification level: 0=muted, 1=normal, 2=tracking (default), 3=watching",
        ),
    ] = 2,
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

