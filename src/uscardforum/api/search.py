"""Search API module for forum search."""

from __future__ import annotations

from typing import Any

from uscardforum.api.base import BaseAPI
from uscardforum.models.search import SearchResult


class SearchAPI(BaseAPI):
    """API for forum search operations.

    Handles:
    - Full-text search with Discourse query operators
    - Search result parsing
    """

    # Allowed sort orders
    ALLOWED_ORDERS = frozenset({
        "relevance",
        "latest",
        "views",
        "likes",
        "op_likes",
        "posts",
        "activity",
    })

    def search(
        self,
        query: str,
        *,
        page: int | None = None,
        order: str | None = None,
    ) -> SearchResult:
        """Search the forum.

        Args:
            query: Search query string. Supports Discourse operators:
                - Basic: "chase sapphire bonus"
                - In title: "chase in:title"
                - By author: "@username"
                - Category: "category:credit-cards"
                - Tag: "#amex"
                - Exact phrase: '"sign up bonus"'
                - Exclude: "chase -sapphire"
                - Time: "after:2024-01-01"

            page: Optional page number for pagination
            order: Optional sort order (relevance, latest, views, likes, etc.)

        Returns:
            Search results with posts, topics, and users
        """
        q = query

        # Add order to query if specified
        if order:
            ord_value = order.split(":", 1)[-1] if "order:" in order else order
            if ord_value not in self.ALLOWED_ORDERS:
                raise ValueError(
                    f"order must be one of {sorted(self.ALLOWED_ORDERS)}"
                )
            if "order:" not in q:
                q = f"{q} order:{ord_value}"

        params_list: list[tuple[str, Any]] = [("q", q)]
        if page is not None:
            params_list.append(("page", int(page)))

        payload = self._get("/search.json", params=params_list)
        return SearchResult.from_api_response(payload)

