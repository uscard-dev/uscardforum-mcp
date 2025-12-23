"""MCP tools for creating topics and posts.

These tools are DISABLED by default for safety. To enable them, set the
environment variable NITAN_WRITE_ENABLED=true or NITAN_WRITE_ENABLED=1.
"""
from __future__ import annotations

import os
from typing import Annotated

from pydantic import Field

from uscardforum.models.topics import CreatedPost, CreatedTopic
from uscardforum.server_core import get_client, mcp


def _is_write_enabled() -> bool:
    """Check if write functionality is enabled via environment variable."""
    value = os.environ.get("NITAN_WRITE_ENABLED", "").lower()
    return value in ("true", "1", "yes", "on")


def _require_write_enabled() -> None:
    """Raise an error if write functionality is not enabled."""
    if not _is_write_enabled():
        raise RuntimeError(
            "Write functionality is disabled. Set NITAN_WRITE_ENABLED=true to enable."
        )


# Only register tools if write functionality is enabled at import time
if _is_write_enabled():

    @mcp.tool()
    def create_topic(
        title: Annotated[
            str,
            Field(description="Title of the new topic"),
        ],
        raw: Annotated[
            str,
            Field(description="Content of the first post in markdown format"),
        ],
        category_id: Annotated[
            int | None,
            Field(default=None, description="Category ID to post in (optional)"),
        ] = None,
        tags: Annotated[
            list[str] | None,
            Field(default=None, description="List of tags for the topic (optional)"),
        ] = None,
    ) -> CreatedTopic:
        """
        Create a new topic on USCardForum. REQUIRES AUTHENTICATION.

        Args:
            title: Title of the new topic
            raw: Content of the first post in markdown format
            category_id: Category ID to post in (optional)
            tags: List of tags for the topic (optional)

        IMPORTANT: This tool requires authentication. Make sure to login first
        using the login() tool or by setting NITAN_USERNAME and NITAN_PASSWORD
        environment variables.

        Returns a CreatedTopic object with:
        - topic_id: ID of the created topic
        - topic_slug: URL slug of the topic
        - post_id: ID of the first post
        - post_number: Always 1 for new topics

        Use get_categories() to find valid category IDs.
        """
        _require_write_enabled()
        return get_client().create_topic(
            title=title,
            raw=raw,
            category_id=category_id,
            tags=tags,
        )

    @mcp.tool()
    def create_post(
        topic_id: Annotated[
            int,
            Field(description="Topic ID to reply to"),
        ],
        raw: Annotated[
            str,
            Field(description="Content of the post in markdown format"),
        ],
        reply_to_post_number: Annotated[
            int | None,
            Field(
                default=None,
                description="Post number to reply to directly (optional, for threaded replies)",
            ),
        ] = None,
    ) -> CreatedPost:
        """
        Create a new post/reply in an existing topic. REQUIRES AUTHENTICATION.

        Args:
            topic_id: Topic ID to reply to
            raw: Content of the post in markdown format
            reply_to_post_number: Post number to reply to directly (optional)

        IMPORTANT: This tool requires authentication. Make sure to login first
        using the login() tool or by setting NITAN_USERNAME and NITAN_PASSWORD
        environment variables.

        Returns a CreatedPost object with:
        - post_id: ID of the created post
        - post_number: Position in the topic
        - topic_id: ID of the topic
        - topic_slug: URL slug of the topic

        Use get_topic_info() to get the topic ID from a topic URL.
        """
        _require_write_enabled()
        return get_client().create_post(
            topic_id=topic_id,
            raw=raw,
            reply_to_post_number=reply_to_post_number,
        )

    __all__ = ["create_topic", "create_post"]

else:
    # When write is disabled, export empty list
    __all__ = []

