"""Domain models for USCardForum.

This package contains all the Pydantic models representing domain entities
returned by the Discourse API.
"""

from uscardforum.models.auth import (
    Bookmark,
    LoginResult,
    Notification,
    Session,
    SubscriptionResult,
)
from uscardforum.models.categories import Category
from uscardforum.models.search import SearchPost, SearchResult, SearchTopic
from uscardforum.models.topics import (
    CreatedPost,
    CreatedTopic,
    Post,
    Topic,
    TopicInfo,
    TopicSummary,
)
from uscardforum.models.users import (
    Badge,
    BadgeInfo,
    FollowList,
    UserAction,
    UserBadges,
    UserReactions,
    UserSummary,
)

__all__ = [
    # Topics
    "Topic",
    "TopicSummary",
    "TopicInfo",
    "Post",
    "CreatedTopic",
    "CreatedPost",
    # Users
    "UserSummary",
    "UserAction",
    "Badge",
    "BadgeInfo",
    "UserBadges",
    "UserReactions",
    "FollowList",
    # Search
    "SearchResult",
    "SearchPost",
    "SearchTopic",
    # Categories
    "Category",
    # Auth
    "Session",
    "Notification",
    "Bookmark",
    "LoginResult",
    "SubscriptionResult",
]

