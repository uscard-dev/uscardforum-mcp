"""USCardForum - MCP Server for Discourse Forum Interaction.

A comprehensive MCP server for interacting with USCardForum,
a Discourse-based community for US credit card discussions.

Example:
    ```python
    from uscardforum import DiscourseClient

    client = DiscourseClient()

    # Browse hot topics
    for topic in client.get_hot_topics():
        print(f"{topic.title} ({topic.posts_count} posts)")

    # Search
    results = client.search("Chase Sapphire")
    for post in results.posts:
        print(post.blurb)
    ```
"""

__version__ = "0.1.0"

# Main client
from uscardforum.client import DiscourseClient

# Domain models
from uscardforum.models import (
    Badge,
    BadgeInfo,
    Bookmark,
    # Categories
    Category,
    FollowList,
    LoginResult,
    Notification,
    Post,
    SearchPost,
    # Search
    SearchResult,
    SearchTopic,
    # Auth
    Session,
    SubscriptionResult,
    # Topics
    Topic,
    TopicInfo,
    TopicSummary,
    UserAction,
    UserBadges,
    UserReactions,
    # Users
    UserSummary,
)

# Cloudflare utilities
from uscardforum.utils.cloudflare import (
    create_cloudflare_session,
    create_cloudflare_session_with_fallback,
)

__all__ = [
    # Version
    "__version__",
    # Client
    "DiscourseClient",
    # Cloudflare utilities
    "create_cloudflare_session",
    "create_cloudflare_session_with_fallback",
    # Topic models
    "Topic",
    "TopicSummary",
    "TopicInfo",
    "Post",
    # User models
    "UserSummary",
    "UserAction",
    "Badge",
    "BadgeInfo",
    "UserBadges",
    "UserReactions",
    "FollowList",
    # Search models
    "SearchResult",
    "SearchPost",
    "SearchTopic",
    # Category models
    "Category",
    # Auth models
    "Session",
    "Notification",
    "Bookmark",
    "LoginResult",
    "SubscriptionResult",
]
