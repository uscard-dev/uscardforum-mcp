"""Categories API module for forum categories."""

from __future__ import annotations

from typing import Any

from uscardforum.api.base import BaseAPI
from uscardforum.models.categories import Category, CategoryMap


class CategoriesAPI(BaseAPI):
    """API for category operations.

    Handles:
    - Fetching category list
    - Category ID to name mapping
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._category_cache: dict[int, str] | None = None

    def get_categories(self) -> list[Category]:
        """Fetch all forum categories.

        Returns:
            List of category objects (including subcategories)
        """
        payload = self._get("/categories.json")
        category_list = payload.get("category_list", {}).get("categories", [])

        categories: list[Category] = []
        for cat in category_list:
            categories.append(Category(
                id=cat.get("id", 0),
                name=cat.get("name", ""),
                slug=cat.get("slug"),
                description=cat.get("description"),
                topic_count=cat.get("topic_count", 0),
                post_count=cat.get("post_count", 0),
                parent_category_id=None,
                color=cat.get("color"),
            ))

            # Process subcategories
            subs = cat.get("subcategory_list") or cat.get("subcategories") or []
            for sub in subs:
                categories.append(Category(
                    id=sub.get("id", 0),
                    name=sub.get("name", ""),
                    slug=sub.get("slug"),
                    description=sub.get("description"),
                    topic_count=sub.get("topic_count", 0),
                    post_count=sub.get("post_count", 0),
                    parent_category_id=cat.get("id"),
                    color=sub.get("color"),
                ))

        return categories

    def get_category_map(self, use_cache: bool = True) -> CategoryMap:
        """Get mapping of category IDs to names.

        Args:
            use_cache: Use cached map if available (default: True)

        Returns:
            CategoryMap with ID to name mapping
        """
        if use_cache and self._category_cache is not None:
            return CategoryMap(categories=self._category_cache)

        categories = self.get_categories()
        mapping = {cat.id: cat.name for cat in categories}
        self._category_cache = mapping
        return CategoryMap(categories=mapping)

    def clear_cache(self) -> None:
        """Clear the category cache."""
        self._category_cache = None

