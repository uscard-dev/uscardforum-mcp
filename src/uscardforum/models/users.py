"""Domain models for users and their activity."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class UserAction(BaseModel):
    """A user activity entry (reply, like, etc.)."""

    action_type: int | None = Field(None, description="Type of action")
    topic_id: int | None = Field(None, description="Related topic ID")
    post_number: int | None = Field(None, description="Related post number")
    title: str | None = Field(None, description="Topic title")
    excerpt: str | None = Field(None, description="Content preview")
    created_at: datetime | None = Field(None, description="When action occurred")
    username: str | None = Field(None, description="Username who performed action")
    acting_username: str | None = Field(None, description="Acting user")

    class Config:
        extra = "ignore"


class Badge(BaseModel):
    """A single badge instance."""

    id: int = Field(..., description="Badge instance ID")
    badge_id: int = Field(..., description="Badge type ID")
    name: str = Field(..., description="Badge name")
    description: str | None = Field(None, description="Badge description")
    granted_at: datetime | None = Field(None, description="When earned")
    badge_type_id: int | None = Field(None, description="Badge category")

    class Config:
        extra = "ignore"


class BadgeInfo(BaseModel):
    """Badge type information."""

    id: int = Field(..., description="Badge type ID")
    name: str = Field(..., description="Badge name")
    description: str | None = Field(None, description="Badge description")
    icon: str | None = Field(None, description="Badge icon")
    badge_type_id: int | None = Field(None, description="Badge category")

    class Config:
        extra = "ignore"


class UserBadges(BaseModel):
    """User's badges with metadata."""

    badges: list[Badge] = Field(default_factory=list, description="Earned badges")
    badge_types: list[BadgeInfo] = Field(
        default_factory=list, description="Badge type info"
    )

    class Config:
        extra = "ignore"


class UserStats(BaseModel):
    """User statistics."""

    posts_read_count: int = Field(0, description="Posts read")
    topics_entered: int = Field(0, description="Topics viewed")
    likes_given: int = Field(0, description="Likes given")
    likes_received: int = Field(0, description="Likes received")
    days_visited: int = Field(0, description="Days visited")
    post_count: int = Field(0, description="Posts created")
    topic_count: int = Field(0, description="Topics created")

    class Config:
        extra = "ignore"


class UserSummary(BaseModel):
    """Comprehensive user profile summary."""

    user_id: int | None = Field(None, description="User ID")
    username: str | None = Field(None, description="Username")
    name: str | None = Field(None, description="Display name")
    created_at: datetime | None = Field(None, description="Account creation date")
    last_seen_at: datetime | None = Field(None, description="Last seen online")
    stats: UserStats | None = Field(None, description="User statistics")
    badges: list[Badge] = Field(default_factory=list, description="Recent badges")
    top_topics: list[Any] = Field(default_factory=list, description="Top topics")
    top_replies: list[Any] = Field(default_factory=list, description="Top replies")

    class Config:
        extra = "ignore"


class FollowUser(BaseModel):
    """A user in a follow list."""

    id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    name: str | None = Field(None, description="Display name")
    avatar_template: str | None = Field(None, description="Avatar URL template")

    class Config:
        extra = "ignore"


class FollowList(BaseModel):
    """List of followed/following users."""

    users: list[FollowUser] = Field(default_factory=list, description="User list")
    total_count: int = Field(0, description="Total users")

    class Config:
        extra = "ignore"


class UserReactions(BaseModel):
    """User's post reactions."""

    reactions: list[Any] = Field(default_factory=list, description="Reaction data")

    class Config:
        extra = "ignore"

