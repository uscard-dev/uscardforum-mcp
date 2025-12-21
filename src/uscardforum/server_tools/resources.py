"""MCP resources for quick data access."""
from __future__ import annotations

import json

from uscardforum.server_core import get_client, mcp


@mcp.resource("forum://categories")
def resource_categories() -> str:
    """Forum category ID to name mapping."""
    client = get_client()
    category_map = client.get_category_map()
    return json.dumps(dict(category_map.categories), indent=2)


@mcp.resource("forum://hot-topics")
def resource_hot_topics() -> str:
    """Currently trending topics on the forum."""
    client = get_client()
    topics = client.get_hot_topics()
    simplified = [
        {
            "id": t.id,
            "title": t.title,
            "posts_count": t.posts_count,
            "views": t.views,
            "like_count": t.like_count,
        }
        for t in topics[:20]  # Limit to top 20
    ]
    return json.dumps(simplified, indent=2)


@mcp.resource("forum://new-topics")
def resource_new_topics() -> str:
    """Latest new topics on the forum."""
    client = get_client()
    topics = client.get_new_topics()
    simplified = [
        {
            "id": t.id,
            "title": t.title,
            "posts_count": t.posts_count,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in topics[:20]  # Limit to top 20
    ]
    return json.dumps(simplified, indent=2)


__all__ = [
    "resource_categories",
    "resource_hot_topics",
    "resource_new_topics",
]

