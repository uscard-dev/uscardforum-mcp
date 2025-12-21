"""MCP tools for topic discovery and content."""
from __future__ import annotations

from uscardforum.models.topics import Post, TopicInfo, TopicSummary
from uscardforum.server_core import get_client, mcp


@mcp.tool()
def get_hot_topics() -> list[TopicSummary]:
    """
    Fetch currently trending/hot topics from USCardForum.

    This returns the most actively discussed topics right now, ranked by
    engagement metrics like recent replies, views, and likes.

    Use this to:
    - See what the community is currently discussing
    - Find breaking news or time-sensitive opportunities
    - Discover popular ongoing discussions

    Returns a list of TopicSummary objects with fields:
    - id: Topic ID (use with get_topic_posts)
    - title: Topic title
    - posts_count: Total replies
    - views: View count
    - like_count: Total likes
    - created_at: Creation timestamp
    - last_posted_at: Last activity timestamp

    Example response interpretation:
    A topic with high views but low posts may be informational.
    A topic with many recent posts is actively being discussed.
    """
    return get_client().get_hot_topics()


@mcp.tool()
def get_new_topics() -> list[TopicSummary]:
    """
    Fetch the latest/newest topics from USCardForum.

    Returns recently created topics sorted by creation time (newest first).
    These may have fewer replies but contain fresh information.

    Use this to:
    - Find newly posted deals or offers
    - See fresh questions from the community
    - Discover emerging discussions before they get popular

    Returns a list of TopicSummary objects with:
    - id: Topic ID
    - title: Topic title
    - posts_count: Number of posts
    - created_at: When the topic was created
    - category_id: Which forum section it's in

    Tip: New topics with high view counts may indicate important news.
    """
    return get_client().get_new_topics()


@mcp.tool()
def get_top_topics(period: str = "monthly") -> list[TopicSummary]:
    """
    Fetch top-performing topics for a specific time period.

    Args:
        period: Time window for ranking. Must be one of:
            - "daily": Top topics from today
            - "weekly": Top topics this week
            - "monthly": Top topics this month (default)
            - "quarterly": Top topics this quarter
            - "yearly": Top topics this year

    Use this to:
    - Find the most valuable discussions in a time range
    - Research historically important threads
    - Identify evergreen popular content

    Returns TopicSummary objects sorted by engagement score.

    Example: Use "yearly" to find the most impactful discussions,
    or "daily" to see what's trending today.
    """
    return get_client().get_top_topics(period=period)


@mcp.tool()
def get_topic_info(topic_id: int) -> TopicInfo:
    """
    Get metadata about a specific topic without fetching all posts.

    Args:
        topic_id: The numeric topic ID (from URLs like /t/slug/12345)

    Use this FIRST before reading a topic to:
    - Check how many posts it contains (for pagination planning)
    - Get the topic title and timestamps
    - Decide whether to fetch all posts or paginate

    Returns a TopicInfo object with:
    - topic_id: The topic ID
    - title: Full topic title
    - post_count: Total number of posts
    - highest_post_number: Last post number (may differ from count if posts deleted)
    - last_posted_at: When the last reply was made

    Strategy for large topics:
    - <50 posts: Safe to fetch all at once
    - 50-200 posts: Consider using max_posts parameter
    - >200 posts: Fetch in batches or summarize key posts
    """
    return get_client().get_topic_info(topic_id)


@mcp.tool()
def get_topic_posts(
    topic_id: int,
    post_number: int = 1,
    include_raw: bool = False,
) -> list[Post]:
    """
    Fetch a batch of posts from a topic starting at a specific position.

    Args:
        topic_id: The numeric topic ID
        post_number: Which post number to start from (default: 1 = first post)
        include_raw: Include raw markdown source (default: False, returns HTML)

    This fetches ~20 posts per call starting from post_number.
    Use for paginated reading of topics.

    Returns a list of Post objects with:
    - post_number: Position in topic (1, 2, 3...)
    - username: Author's username
    - cooked: HTML content of the post
    - raw: Markdown source (if include_raw=True)
    - created_at: When posted
    - updated_at: Last edit time
    - like_count: Number of likes
    - reply_count: Number of direct replies
    - reply_to_post_number: Which post this replies to (if any)

    Pagination example:
    1. Call with post_number=1, get posts 1-20
    2. Call with post_number=21, get posts 21-40
    3. Continue until no posts returned
    """
    return get_client().get_topic_posts(
        topic_id, post_number=post_number, include_raw=include_raw
    )


@mcp.tool()
def get_all_topic_posts(
    topic_id: int,
    include_raw: bool = False,
    start_post_number: int = 1,
    end_post_number: int | None = None,
    max_posts: int | None = None,
) -> list[Post]:
    """
    Fetch all posts from a topic with automatic pagination.

    Args:
        topic_id: The numeric topic ID
        include_raw: Include markdown source (default: False)
        start_post_number: First post to fetch (default: 1)
        end_post_number: Last post to fetch (optional, fetches to end if not set)
        max_posts: Maximum number of posts to return (optional safety limit)

    This automatically handles pagination to fetch multiple batches.

    IMPORTANT: For topics with many posts (>100), use max_posts to limit
    the response size. You can always fetch more with start_post_number.

    Use cases:
    - Fetch entire small topic: get_all_topic_posts(topic_id=123)
    - Fetch first 50 posts: get_all_topic_posts(topic_id=123, max_posts=50)
    - Fetch posts 51-100: get_all_topic_posts(topic_id=123, start_post_number=51, max_posts=50)
    - Fetch specific range: get_all_topic_posts(topic_id=123, start=10, end=30)

    Returns the same Post structure as get_topic_posts but for all matching posts.

    Pro tip: Use get_topic_info first to check post_count before deciding
    whether to fetch all or paginate manually.
    """
    return get_client().get_all_topic_posts(
        topic_id,
        include_raw=include_raw,
        start_post_number=start_post_number,
        end_post_number=end_post_number,
        max_posts=max_posts,
    )


__all__ = [
    "get_hot_topics",
    "get_new_topics",
    "get_top_topics",
    "get_topic_info",
    "get_topic_posts",
    "get_all_topic_posts",
]

