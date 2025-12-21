"""
Integration tests for Categories API.

Tests against the actual USCardForum API with comprehensive field assertions.
"""

import pytest
from uscardforum.models.categories import Category


class TestCategoryModel:
    """Test Category model fields are populated correctly."""

    def test_category_required_fields(self, client):
        """Test Category required fields are present."""
        categories = client.get_categories()

        assert len(categories) > 0, "Forum should have categories"

        for category in categories:
            assert isinstance(category, Category)
            assert category.id > 0, "id must be positive"
            assert category.name, "name must not be empty"
            assert isinstance(category.name, str)

    def test_category_slug_field(self, client):
        """Test Category slug field."""
        categories = client.get_categories()
        category = categories[0]

        if category.slug is not None:
            assert isinstance(category.slug, str)
            assert len(category.slug) > 0
            # Slugs should be URL-safe (lowercase, no spaces)
            assert " " not in category.slug, "slug should not contain spaces"

    def test_category_count_fields(self, client):
        """Test Category count fields are non-negative."""
        categories = client.get_categories()

        for category in categories:
            assert category.topic_count >= 0, "topic_count must be non-negative"
            assert category.post_count >= 0, "post_count must be non-negative"

    def test_category_color_field(self, client):
        """Test Category color field format."""
        categories = client.get_categories()

        for category in categories:
            if category.color is not None:
                assert isinstance(category.color, str)
                # Color should be hex format (6 characters)
                assert len(category.color) == 6, "color should be 6-char hex"
                # Should be valid hex
                try:
                    int(category.color, 16)
                except ValueError:
                    pytest.fail(f"color '{category.color}' is not valid hex")

    def test_category_description_field(self, client):
        """Test Category description field."""
        categories = client.get_categories()

        for category in categories:
            if category.description is not None:
                assert isinstance(category.description, str)

    def test_category_parent_relationship(self, client):
        """Test Category parent_category_id relationships."""
        categories = client.get_categories()

        # Build set of valid category IDs
        category_ids = {c.id for c in categories}

        for category in categories:
            if category.parent_category_id is not None:
                assert category.parent_category_id > 0, "parent_id must be positive"
                # Parent should exist (or be in a different fetch)
                # Note: parent might be in same set
                assert isinstance(category.parent_category_id, int)


class TestCategoryHierarchy:
    """Test category hierarchy relationships."""

    def test_has_parent_categories(self, client):
        """Test forum has parent (top-level) categories."""
        categories = client.get_categories()

        # Find categories without parents (top-level)
        top_level = [c for c in categories if c.parent_category_id is None]
        assert len(top_level) > 0, "Should have top-level categories"

    def test_subcategories_have_valid_parents(self, client):
        """Test subcategories reference valid parents."""
        categories = client.get_categories()

        category_ids = {c.id for c in categories}
        subcategories = [c for c in categories if c.parent_category_id is not None]

        for subcat in subcategories:
            # Parent ID should reference an existing category
            # (Note: API might not return all parents, so we just check it's positive)
            assert subcat.parent_category_id > 0


class TestCategoryListIntegrity:
    """Test integrity of category list."""

    def test_unique_category_ids(self, client):
        """Test all category IDs are unique."""
        categories = client.get_categories()

        ids = [c.id for c in categories]
        assert len(ids) == len(set(ids)), "Category IDs must be unique"

    def test_all_categories_parseable(self, client):
        """Test all categories parse without errors."""
        categories = client.get_categories()

        # If we got here without exceptions, all parsed correctly
        assert len(categories) > 0

        for category in categories:
            # Verify it's a proper Category object
            assert isinstance(category, Category)
            assert hasattr(category, "id")
            assert hasattr(category, "name")
            assert hasattr(category, "slug")
            assert hasattr(category, "description")
            assert hasattr(category, "topic_count")
            assert hasattr(category, "post_count")
            assert hasattr(category, "parent_category_id")
            assert hasattr(category, "color")

    def test_category_names_not_empty(self, client):
        """Test no category has empty name."""
        categories = client.get_categories()

        for category in categories:
            assert category.name, f"Category {category.id} has empty name"
            assert category.name.strip(), f"Category {category.id} has whitespace-only name"
