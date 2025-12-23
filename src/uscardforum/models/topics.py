"""Domain models for topics and posts."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class TopicSummary(BaseModel):
    """Summary of a topic for list views (hot, new, top topics)."""

    id: int = Field(..., description="Unique topic identifier")
    title: str = Field(..., description="Topic title")
    posts_count: int = Field(0, description="Total number of posts")
    views: int = Field(0, description="Total view count")
    like_count: int = Field(0, description="Total likes on the topic")
    category_id: int | None = Field(None, description="Category identifier")
    category_name: str | None = Field(None, description="Category name")
    created_at: datetime | None = Field(None, description="When topic was created")
    last_posted_at: datetime | None = Field(None, description="Last activity time")

    class Config:
        extra = "ignore"


class TopicInfo(BaseModel):
    """Detailed topic metadata."""

    topic_id: int = Field(..., description="Topic identifier")
    title: str | None = Field(None, description="Topic title")
    post_count: int = Field(0, description="Total number of posts")
    highest_post_number: int = Field(0, description="Highest post number")
    last_posted_at: datetime | None = Field(None, description="Last activity time")

    class Config:
        extra = "ignore"


class Post(BaseModel):
    """A single post within a topic."""

    id: int = Field(..., description="Unique post identifier")
    post_number: int = Field(..., description="Position in topic (1-indexed)")
    username: str = Field(..., description="Author's username")
    cooked: str | None = Field(None, description="HTML-rendered content")
    raw: str | None = Field(None, description="Raw markdown source")
    created_at: datetime | None = Field(None, description="When posted")
    updated_at: datetime | None = Field(None, description="Last edit time")
    like_count: int = Field(0, description="Number of likes")
    reply_count: int = Field(0, description="Number of direct replies")
    reply_to_post_number: int | None = Field(
        None, description="Post number this replies to"
    )

    class Config:
        extra = "ignore"


class Topic(BaseModel):
    """Full topic with metadata and posts."""

    id: int = Field(..., description="Topic identifier")
    title: str = Field(..., description="Topic title")
    posts_count: int = Field(0, description="Total posts")
    views: int = Field(0, description="View count")
    like_count: int = Field(0, description="Total likes")
    category_id: int | None = Field(None, description="Category ID")
    category_name: str | None = Field(None, description="Category name")
    created_at: datetime | None = Field(None, description="Creation time")
    last_posted_at: datetime | None = Field(None, description="Last activity")
    posts: list[Post] = Field(default_factory=list, description="Posts in topic")

    class Config:
        extra = "ignore"


class CreatedTopic(BaseModel):
    """Response when a new topic is successfully created."""

    topic_id: int = Field(..., description="ID of the created topic")
    topic_slug: str = Field(..., description="URL slug of the created topic")
    post_id: int = Field(..., description="ID of the first post in the topic")
    post_number: int = Field(1, description="Post number (always 1 for new topics)")

    class Config:
        extra = "ignore"

    @classmethod
    def from_api_response(cls, data: dict) -> CreatedTopic:
        """Parse API response into CreatedTopic."""
        return cls(
            topic_id=data.get("topic_id", 0),
            topic_slug=data.get("topic_slug", ""),
            post_id=data.get("id", 0),
            post_number=data.get("post_number", 1),
        )


class CreatedPost(BaseModel):
    """Response when a new post/reply is successfully created."""

    post_id: int = Field(..., description="ID of the created post")
    post_number: int = Field(..., description="Position in the topic")
    topic_id: int = Field(..., description="ID of the topic")
    topic_slug: str = Field(..., description="URL slug of the topic")

    class Config:
        extra = "ignore"

    @classmethod
    def from_api_response(cls, data: dict) -> CreatedPost:
        """Parse API response into CreatedPost."""
        return cls(
            post_id=data.get("id", 0),
            post_number=data.get("post_number", 0),
            topic_id=data.get("topic_id", 0),
            topic_slug=data.get("topic_slug", ""),
        )

