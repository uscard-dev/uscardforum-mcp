"""Domain models for search results."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SearchPost(BaseModel):
    """A post in search results."""

    id: int = Field(..., description="Post ID")
    topic_id: int = Field(..., description="Parent topic ID")
    post_number: int = Field(..., description="Position in topic")
    username: str | None = Field(None, description="Author username")
    blurb: str | None = Field(None, description="Content excerpt with highlights")
    created_at: datetime | None = Field(None, description="When posted")
    like_count: int = Field(0, description="Number of likes")

    class Config:
        extra = "ignore"


class SearchTopic(BaseModel):
    """A topic in search results."""

    id: int = Field(..., description="Topic ID")
    title: str = Field(..., description="Topic title")
    posts_count: int = Field(0, description="Number of posts")
    views: int = Field(0, description="View count")
    like_count: int = Field(0, description="Total likes")
    category_id: int | None = Field(None, description="Category ID")
    category_name: str | None = Field(None, description="Category name")
    created_at: datetime | None = Field(None, description="Creation time")

    class Config:
        extra = "ignore"


class SearchUser(BaseModel):
    """A user in search results."""

    id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    name: str | None = Field(None, description="Display name")
    avatar_template: str | None = Field(None, description="Avatar URL")

    class Config:
        extra = "ignore"


class GroupedSearchResult(BaseModel):
    """Metadata about search result counts."""

    post_ids: list[int] = Field(default_factory=list, description="Matching post IDs")
    topic_ids: list[int] = Field(default_factory=list, description="Matching topic IDs")
    user_ids: list[int] = Field(default_factory=list, description="Matching user IDs")
    more_posts: bool | None = Field(None, description="More posts available")
    more_topics: bool | None = Field(None, description="More topics available")

    class Config:
        extra = "ignore"


class SearchResult(BaseModel):
    """Complete search results."""

    posts: list[SearchPost] = Field(default_factory=list, description="Matching posts")
    topics: list[SearchTopic] = Field(
        default_factory=list, description="Matching topics"
    )
    users: list[SearchUser] = Field(default_factory=list, description="Matching users")
    grouped_search_result: GroupedSearchResult | None = Field(
        None, description="Result metadata"
    )

    class Config:
        extra = "ignore"

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> SearchResult:
        """Parse from raw API response."""
        posts = [SearchPost(**p) for p in data.get("posts", [])]
        topics = [SearchTopic(**t) for t in data.get("topics", [])]
        users = [SearchUser(**u) for u in data.get("users", [])]

        grouped = None
        if "grouped_search_result" in data:
            grouped = GroupedSearchResult(**data["grouped_search_result"])

        return cls(
            posts=posts,
            topics=topics,
            users=users,
            grouped_search_result=grouped,
        )

