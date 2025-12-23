"""
MCP Tools, Prompts, and Resources for USCardForum.

Tools are organized into 5 logical groups:

📰 Discovery (5 tools) — Find content to read
    get_hot_topics, get_new_topics, get_top_topics, search_forum, get_categories

📖 Reading (3 tools) — Access topic content
    get_topic_info, get_topic_posts, get_all_topic_posts

👤 Users (9 tools) — Profile & activity research
    get_user_summary, get_user_topics, get_user_replies, get_user_actions,
    get_user_badges, get_user_following, get_user_followers, get_user_reactions,
    list_users_with_badge

🔐 Auth (5 tools) — Authenticated actions (requires login)
    login, get_current_session, get_notifications, bookmark_post, subscribe_topic

✏️ Write (2 tools) — Create content (DISABLED by default, set NITAN_WRITE_ENABLED=true)
    create_topic, create_post
"""
from __future__ import annotations

# =============================================================================
# ✏️ Write — Create content (disabled by default)
# =============================================================================
# Import write module to trigger conditional tool registration
from . import write as _write_module

# =============================================================================
# 🔐 Auth — Authenticated actions (requires login)
# =============================================================================
from .auth import (
    bookmark_post,
    get_current_session,
    get_notifications,
    login,
    subscribe_topic,
)
from .categories import get_categories

# =============================================================================
# Prompts & Resources
# =============================================================================
from .prompts import analyze_user, compare_cards, find_data_points, research_topic
from .resources import resource_categories, resource_hot_topics, resource_new_topics
from .search import search_forum

# =============================================================================
# 📰 Discovery — Find content to read
# =============================================================================
# =============================================================================
# 📖 Reading — Access topic content
# =============================================================================
from .topics import (
    get_all_topic_posts,
    get_hot_topics,
    get_new_topics,
    get_top_topics,
    get_topic_info,
    get_topic_posts,
)

# =============================================================================
# 👤 Users — Profile & activity research
# =============================================================================
from .users import (
    get_user_actions,
    get_user_badges,
    get_user_followers,
    get_user_following,
    get_user_reactions,
    get_user_replies,
    get_user_summary,
    get_user_topics,
    list_users_with_badge,
)

__all__ = [
    # 📰 Discovery
    "get_hot_topics",
    "get_new_topics",
    "get_top_topics",
    "search_forum",
    "get_categories",
    # 📖 Reading
    "get_topic_info",
    "get_topic_posts",
    "get_all_topic_posts",
    # 👤 Users
    "get_user_summary",
    "get_user_topics",
    "get_user_replies",
    "get_user_actions",
    "get_user_badges",
    "get_user_following",
    "get_user_followers",
    "get_user_reactions",
    "list_users_with_badge",
    # 🔐 Auth
    "login",
    "get_current_session",
    "get_notifications",
    "bookmark_post",
    "subscribe_topic",
    # Prompts
    "analyze_user",
    "compare_cards",
    "find_data_points",
    "research_topic",
    # Resources
    "resource_categories",
    "resource_hot_topics",
    "resource_new_topics",
]

# Add write tools to __all__ if enabled
__all__.extend(_write_module.__all__)

