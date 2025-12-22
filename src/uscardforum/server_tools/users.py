"""MCP tools for user profiles and activity."""
from __future__ import annotations

from typing import Annotated, Any

from pydantic import Field

from uscardforum.models.users import (
    FollowList,
    UserAction,
    UserBadges,
    UserReactions,
    UserSummary,
)
from uscardforum.server_core import get_client, mcp


@mcp.tool()
def get_user_summary(
    username: Annotated[
        str,
        Field(description="The user's handle (case-insensitive)"),
    ],
) -> UserSummary:
    """
    Fetch a comprehensive summary of a user's profile.

    Args:
        username: The user's handle (case-insensitive)

    Returns a UserSummary object with:
    - user_id: User ID
    - username: Username
    - stats: UserStats with posts, topics, likes given/received, etc.
    - badges: List of recent Badge objects
    - top_topics: Most successful topics
    - top_replies: Most successful replies

    Use this to:
    - Evaluate a user's credibility and experience
    - Find their most valuable contributions
    - Understand their participation level

    The summary provides a quick overview without fetching
    individual post histories.
    """
    return get_client().get_user_summary(username)


@mcp.tool()
def get_user_topics(
    username: Annotated[
        str,
        Field(description="The user's handle"),
    ],
    page: Annotated[
        int | None,
        Field(default=None, description="Page number for pagination"),
    ] = None,
) -> list[dict[str, Any]]:
    """
    Fetch topics created by a specific user.

    Args:
        username: The user's handle
        page: Page number for pagination (optional)

    Returns a list of topic objects with:
    - id: Topic ID
    - title: Topic title
    - posts_count: Number of replies
    - views: View count
    - created_at: When created
    - category_id: Forum category

    Use this to:
    - See what discussions a user has initiated
    - Find expert users in specific areas
    - Research a user's areas of interest

    Paginate by incrementing the page parameter.
    """
    return get_client().get_user_topics(username, page=page)


@mcp.tool()
def get_user_replies(
    username: Annotated[
        str,
        Field(description="The user's handle"),
    ],
    offset: Annotated[
        int | None,
        Field(default=None, description="Pagination offset (0, 30, 60, ...)"),
    ] = None,
) -> list[UserAction]:
    """
    Fetch replies/posts made by a user in other topics.

    Args:
        username: The user's handle
        offset: Pagination offset (0, 30, 60, ...)

    Returns a list of UserAction objects with:
    - topic_id: Which topic they replied to
    - post_number: Their post number in that topic
    - title: Topic title
    - excerpt: Preview of their reply
    - created_at: When they replied

    Use this to:
    - See a user's contributions across topics
    - Find their data points and experiences
    - Evaluate the quality of their participation

    Paginate with offset in increments of 30.
    """
    return get_client().get_user_replies(username, offset=offset)


@mcp.tool()
def get_user_actions(
    username: Annotated[
        str,
        Field(description="The user's handle"),
    ],
    filter: Annotated[
        int | None,
        Field(
            default=None,
            description="Action type filter: 1=likes given, 2=likes received, 4=topics created, 5=replies posted, 6=all posts, 7=mentions",
        ),
    ] = None,
    offset: Annotated[
        int | None,
        Field(default=None, description="Pagination offset (0, 30, 60, ...)"),
    ] = None,
) -> list[UserAction]:
    """
    Fetch a user's activity feed with optional filtering.

    Args:
        username: The user's handle
        filter: Action type filter (optional). Common values:
            - 1: Likes given
            - 2: Likes received
            - 4: Topics created
            - 5: Replies posted
            - 6: Posts (all)
            - 7: Mentions
        offset: Pagination offset (0, 30, 60, ...)

    Returns a list of UserAction objects showing what the user has done.

    Use this for detailed activity analysis beyond just replies.
    For most cases, get_user_replies or get_user_topics are simpler.
    """
    return get_client().get_user_actions(username, filter=filter, offset=offset)


@mcp.tool()
def get_user_badges(
    username: Annotated[
        str,
        Field(description="The user's handle"),
    ],
    grouped: Annotated[
        bool,
        Field(default=True, description="Group badges by type (default: True)"),
    ] = True,
) -> UserBadges:
    """
    Fetch badges earned by a user.

    Args:
        username: The user's handle
        grouped: Group badges by type (default: True)

    Returns a UserBadges object with:
    - badges: List of Badge objects with name, description, granted_at
    - badge_types: Badge type information

    Badges indicate:
    - Participation milestones (first post, anniversaries)
    - Community recognition (editor, leader)
    - Special achievements

    Use to assess user experience and trustworthiness.
    """
    return get_client().get_user_badges(username, grouped=grouped)


@mcp.tool()
def get_user_following(
    username: Annotated[
        str,
        Field(description="The user's handle"),
    ],
    page: Annotated[
        int | None,
        Field(default=None, description="Page number for pagination"),
    ] = None,
) -> FollowList:
    """
    Fetch the list of users that a user follows.

    Args:
        username: The user's handle
        page: Page number for pagination (optional)

    Returns a FollowList object with:
    - users: List of FollowUser objects
    - total_count: Total users being followed

    Use to:
    - Discover influential users in the community
    - Find related experts
    - Map social connections
    """
    return get_client().get_user_following(username, page=page)


@mcp.tool()
def get_user_followers(
    username: Annotated[
        str,
        Field(description="The user's handle"),
    ],
    page: Annotated[
        int | None,
        Field(default=None, description="Page number for pagination"),
    ] = None,
) -> FollowList:
    """
    Fetch the list of users following a specific user.

    Args:
        username: The user's handle
        page: Page number for pagination (optional)

    Returns a FollowList object with:
    - users: List of FollowUser objects
    - total_count: Total followers

    A high follower count often indicates an influential
    or helpful community member.
    """
    return get_client().get_user_followers(username, page=page)


@mcp.tool()
def get_user_reactions(
    username: Annotated[
        str,
        Field(description="The user's handle"),
    ],
    offset: Annotated[
        int | None,
        Field(default=None, description="Pagination offset"),
    ] = None,
) -> UserReactions:
    """
    Fetch a user's post reactions (likes, etc.).

    Args:
        username: The user's handle
        offset: Pagination offset (optional)

    Returns a UserReactions object with reaction data.

    Use to see what content a user has reacted to,
    which can indicate their interests and values.
    """
    return get_client().get_user_reactions(username, offset=offset)


@mcp.tool()
def list_users_with_badge(
    badge_id: Annotated[
        int,
        Field(description="The numeric badge ID"),
    ],
    offset: Annotated[
        int | None,
        Field(default=None, description="Pagination offset"),
    ] = None,
) -> dict[str, Any]:
    """
    List all users who have earned a specific badge.

    Args:
        badge_id: The numeric badge ID
        offset: Pagination offset (optional)

    Returns a dictionary with user badge information.

    Use to find community members with specific achievements
    or recognition levels.
    """
    return get_client().list_user_badges(badge_id, offset=offset)


__all__ = [
    "get_user_summary",
    "get_user_topics",
    "get_user_replies",
    "get_user_actions",
    "get_user_badges",
    "get_user_following",
    "get_user_followers",
    "get_user_reactions",
    "list_users_with_badge",
]

