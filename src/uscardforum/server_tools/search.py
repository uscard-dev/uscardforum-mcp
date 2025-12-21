"""MCP tools for search operations."""
from __future__ import annotations

from uscardforum.models.search import SearchResult
from uscardforum.server_core import get_client, mcp


@mcp.tool()
def search_forum(
    query: str,
    page: int | None = None,
    order: str | None = None,
) -> SearchResult:
    """
    Search USCardForum for topics and posts matching a query.

    Args:
        query: Search query string. Supports Discourse operators:
            - Basic: "chase sapphire bonus"
            - In title only: "chase sapphire in:title"
            - By author: "@username chase"
            - In category: "category:credit-cards chase"
            - With tag: "#amex bonus"
            - Exact phrase: '"sign up bonus"'
            - Exclude: "chase -sapphire"
            - Time: "after:2024-01-01" or "before:2024-06-01"

        page: Page number for pagination (starts at 1)

        order: Sort order for results. Options:
            - "relevance": Best match (default)
            - "latest": Most recent first
            - "views": Most viewed
            - "likes": Most liked
            - "activity": Recent activity
            - "posts": Most replies

    Returns a SearchResult object with:
    - posts: List of matching SearchPost objects with excerpts
    - topics: List of matching SearchTopic objects
    - users: List of matching SearchUser objects
    - grouped_search_result: Metadata about result counts

    Example queries:
    - "Chase Sapphire Reserve order:latest" - Recent CSR discussions
    - "AMEX popup in:title" - Topics about AMEX popup in title
    - "data point category:credit-cards" - Data points in CC category
    - "@expert_user order:likes" - Most liked posts by a user

    Pagination: If more results exist, increment page parameter.
    """
    return get_client().search(query, page=page, order=order)


__all__ = ["search_forum"]

