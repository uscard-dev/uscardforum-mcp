"""Domain models for authentication and session management."""

from __future__ import annotations

from datetime import datetime
from enum import IntEnum
from typing import Any

from pydantic import BaseModel, Field


class NotificationLevel(IntEnum):
    """Topic notification levels."""

    MUTED = 0
    NORMAL = 1
    TRACKING = 2
    WATCHING = 3


class AutoDeletePreference(IntEnum):
    """Bookmark auto-delete preferences."""

    NEVER = 0
    WHEN_REMINDER_SENT = 1
    ON_CLICK = 2
    AFTER_THREE_DAYS = 3


class CurrentUser(BaseModel):
    """Current logged-in user information."""

    id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    name: str | None = Field(None, description="Display name")
    avatar_template: str | None = Field(None, description="Avatar URL template")
    unread_notifications: int = Field(0, description="Unread notification count")
    unread_high_priority_notifications: int = Field(
        0, description="High priority unreads"
    )

    class Config:
        extra = "ignore"


class Session(BaseModel):
    """Current session information."""

    current_user: CurrentUser | None = Field(None, description="Logged-in user")
    is_authenticated: bool = Field(False, description="Whether authenticated")

    class Config:
        extra = "ignore"

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> Session:
        """Parse from raw API response."""
        user_data = data.get("current_user") or data.get("user")
        current_user = CurrentUser(**user_data) if user_data else None
        return cls(
            current_user=current_user,
            is_authenticated=current_user is not None,
        )


class Notification(BaseModel):
    """A user notification."""

    id: int = Field(..., description="Notification ID")
    notification_type: int = Field(..., description="Type of notification")
    read: bool = Field(False, description="Whether read")
    created_at: datetime | None = Field(None, description="When created")
    topic_id: int | None = Field(None, description="Related topic ID")
    post_number: int | None = Field(None, description="Related post number")
    slug: str | None = Field(None, description="Topic slug")
    data: dict[str, Any] = Field(default_factory=dict, description="Extra data")

    class Config:
        extra = "ignore"


class LoginResult(BaseModel):
    """Result of a login attempt."""

    success: bool = Field(..., description="Whether login succeeded")
    username: str | None = Field(None, description="Logged-in username")
    error: str | None = Field(None, description="Error message if failed")
    requires_2fa: bool = Field(False, description="Whether 2FA is required")

    class Config:
        extra = "ignore"

    @classmethod
    def from_api_response(
        cls, data: dict[str, Any], username: str
    ) -> LoginResult:
        """Parse from raw API response."""
        if "error" in data:
            return cls(success=False, error=data["error"], username=None, requires_2fa=False)
        if data.get("second_factor_required"):
            return cls(success=False, requires_2fa=True, username=username, error=None)
        return cls(success=True, username=username, error=None, requires_2fa=False)


class Bookmark(BaseModel):
    """A bookmarked post."""

    id: int = Field(..., description="Bookmark ID")
    bookmarkable_id: int = Field(..., description="Bookmarked item ID")
    bookmarkable_type: str = Field("Post", description="Type of bookmarked item")
    name: str | None = Field(None, description="Bookmark label")
    reminder_at: datetime | None = Field(None, description="Reminder time")
    auto_delete_preference: int = Field(3, description="Auto-delete setting")

    class Config:
        extra = "ignore"


class SubscriptionResult(BaseModel):
    """Result of subscribing to a topic."""

    success: bool = Field(..., description="Whether subscription succeeded")
    notification_level: NotificationLevel = Field(
        NotificationLevel.NORMAL, description="New notification level"
    )

    class Config:
        extra = "ignore"

