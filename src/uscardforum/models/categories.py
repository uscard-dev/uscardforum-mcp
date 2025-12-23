"""Domain models for forum categories."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Category(BaseModel):
    """A forum category or subcategory."""

    id: int = Field(..., description="Category ID")
    name: str = Field(..., description="Category name")
    slug: str | None = Field(None, description="URL slug")
    description: str | None = Field(None, description="Category description")
    topic_count: int = Field(0, description="Number of topics")
    post_count: int = Field(0, description="Number of posts")
    parent_category_id: int | None = Field(None, description="Parent category ID")
    color: str | None = Field(None, description="Category color hex")

    class Config:
        extra = "ignore"


class CategoryMap(BaseModel):
    """Mapping of category IDs to names."""

    categories: dict[int, str] = Field(
        default_factory=dict, description="ID to name mapping"
    )

    def get_name(self, category_id: int) -> str | None:
        """Get category name by ID."""
        return self.categories.get(category_id)

    def __getitem__(self, category_id: int) -> str:
        """Get category name by ID."""
        return self.categories[category_id]

    def __contains__(self, category_id: int) -> bool:
        """Check if category ID exists."""
        return category_id in self.categories

    def items(self) -> list[tuple[int, str]]:
        """Iterate over category mappings."""
        return list(self.categories.items())

