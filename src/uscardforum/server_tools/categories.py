"""MCP tools for category lookups."""
from __future__ import annotations

from uscardforum.models.categories import CategoryMap
from uscardforum.server_core import get_client, mcp


@mcp.tool()
def get_categories() -> CategoryMap:
    """
    Get a mapping of all forum categories.

    Returns a CategoryMap object with category_id to category name mapping.
    Categories organize topics by subject area.

    Common USCardForum categories include sections for:
    - Credit card applications and approvals
    - Bank account bonuses
    - Travel and redemptions
    - Data points and experiences

    Use category IDs to:
    - Filter search results by category
    - Understand which section a topic belongs to
    - Navigate to specific areas of interest

    The mapping includes both main categories and subcategories.
    """
    return get_client().get_category_map()


__all__ = ["get_categories"]

