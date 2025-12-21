"""
Integration tests for Topics API.

Tests against the actual USCardForum API with comprehensive field assertions.
"""

import pytest
from datetime import datetime
from uscardforum.models.topics import TopicSummary, TopicInfo, Post


class TestTopicSummaryModel:
    """Test TopicSummary model fields are populated correctly."""

    def test_topic_summary_required_fields(self, client):
        """Test TopicSummary has all required fields populated."""
        topics = client.get_hot_topics()
        assert len(topics) > 0, "Should have hot topics"

        topic = topics[0]
        assert isinstance(topic, TopicSummary)

        # Ensure serialized JSON fields match the TopicSummary domain model
        json_keys = set(topic.model_dump().keys())
        model_keys = set(TopicSummary.model_fields.keys())
        assert json_keys.issubset(model_keys)

        # Required fields must be present
        assert topic.id > 0, "id must be positive integer"
        assert topic.title, "title must not be empty"
        assert isinstance(topic.title, str), "title must be string"

    def test_topic_summary_count_fields(self, client):
        """Test TopicSummary count fields are non-negative integers."""
        topics = client.get_hot_topics()
        topic = topics[0]

        # Count fields should be non-negative
        assert topic.posts_count >= 0, "posts_count must be non-negative"
        assert topic.views >= 0, "views must be non-negative"
        assert topic.like_count >= 0, "like_count must be non-negative"

    def test_topic_summary_optional_fields(self, client):
        """Test TopicSummary optional fields when present."""
        topics = client.get_hot_topics()
        topic = topics[0]

        # Category ID should be present for most topics
        if topic.category_id is not None:
            assert topic.category_id > 0, "category_id must be positive"

        # Timestamps should be datetime when present
        if topic.created_at is not None:
            assert isinstance(topic.created_at, datetime), "created_at must be datetime"

        if topic.last_posted_at is not None:
            assert isinstance(topic.last_posted_at, datetime), "last_posted_at must be datetime"

    def test_topic_summary_from_new_topics(self, client):
        """Test TopicSummary parsing from new topics endpoint."""
        topics = client.get_new_topics()
        assert len(topics) > 0

        for topic in topics[:5]:  # Check first 5
            assert isinstance(topic, TopicSummary)
            assert topic.id > 0
            assert topic.title

    def test_topic_summary_from_top_topics(self, client):
        """Test TopicSummary parsing from top topics endpoint."""
        topics = client.get_top_topics()
        assert len(topics) > 0

        for topic in topics[:5]:
            assert isinstance(topic, TopicSummary)
            assert topic.id > 0
            assert topic.title


class TestTopicInfoModel:
    """Test TopicInfo model fields are populated correctly."""

    def test_topic_info_required_fields(self, client):
        """Test TopicInfo has all required fields."""
        hot = client.get_hot_topics()
        topic_id = hot[0].id

        info = client.get_topic_info(topic_id)
        assert isinstance(info, TopicInfo)

        # The returned JSON should only contain fields defined on TopicInfo
        info_keys = set(info.model_dump().keys())
        model_keys = set(TopicInfo.model_fields.keys())
        assert info_keys.issubset(model_keys)

        # Required fields - note: model uses topic_id not id
        assert info.topic_id == topic_id, "topic_id must match request"
        assert info.post_count >= 1, "post_count must be at least 1"
        assert info.highest_post_number >= 1, "highest_post_number must be at least 1"

    def test_topic_info_field_types(self, client):
        """Test TopicInfo field types."""
        hot = client.get_hot_topics()
        info = client.get_topic_info(hot[0].id)

        assert isinstance(info.topic_id, int)
        assert isinstance(info.post_count, int)
        assert isinstance(info.highest_post_number, int)

    def test_topic_info_optional_fields(self, client):
        """Test TopicInfo optional fields."""
        hot = client.get_hot_topics()
        info = client.get_topic_info(hot[0].id)

        # Title may be present
        if info.title is not None:
            assert isinstance(info.title, str)
            assert len(info.title) > 0

        # Timestamp
        if info.last_posted_at is not None:
            assert isinstance(info.last_posted_at, datetime)

    def test_topic_info_consistency(self, client):
        """Test TopicInfo values are internally consistent."""
        hot = client.get_hot_topics()
        info = client.get_topic_info(hot[0].id)

        # highest_post_number should be >= 1
        # Note: can be > post_count if posts were deleted
        assert info.highest_post_number >= 1
        assert info.post_count >= 1


class TestPostModel:
    """Test Post model fields are populated correctly."""

    def test_post_required_fields(self, client):
        """Test Post has all required fields."""
        hot = client.get_hot_topics()
        posts = client.get_topic_posts(hot[0].id)

        assert len(posts) > 0, "Should have posts"
        post = posts[0]
        assert isinstance(post, Post)

        # The post JSON should not have fields outside the Post domain model
        post_keys = set(post.model_dump().keys())
        model_keys = set(Post.model_fields.keys())
        assert post_keys.issubset(model_keys)

        # Required fields
        assert post.id > 0, "id must be positive"
        assert post.post_number >= 1, "post_number must be at least 1"
        assert post.username, "username must not be empty"
        assert isinstance(post.username, str), "username must be string"

    def test_post_content_fields(self, client):
        """Test Post content fields."""
        hot = client.get_hot_topics()
        posts = client.get_topic_posts(hot[0].id)
        post = posts[0]

        # cooked (HTML content) should be present
        assert post.cooked is not None, "cooked content must be present"
        assert isinstance(post.cooked, str), "cooked must be string"
        assert len(post.cooked) > 0, "cooked should not be empty"

    def test_post_count_fields(self, client):
        """Test Post count fields are non-negative."""
        hot = client.get_hot_topics()
        posts = client.get_topic_posts(hot[0].id)
        post = posts[0]

        assert post.like_count >= 0, "like_count must be non-negative"
        assert post.reply_count >= 0, "reply_count must be non-negative"

    def test_post_timestamp_fields(self, client):
        """Test Post timestamp fields."""
        hot = client.get_hot_topics()
        posts = client.get_topic_posts(hot[0].id)
        post = posts[0]

        if post.created_at is not None:
            assert isinstance(post.created_at, datetime), "created_at must be datetime"

        if post.updated_at is not None:
            assert isinstance(post.updated_at, datetime), "updated_at must be datetime"

    def test_post_reply_reference(self, client):
        """Test Post reply_to_post_number is valid when present."""
        hot = client.get_hot_topics()
        posts = client.get_topic_posts(hot[0].id)

        # Find a reply post
        for post in posts:
            if post.reply_to_post_number is not None:
                assert post.reply_to_post_number >= 1, "reply_to must reference valid post"
                assert post.reply_to_post_number < post.post_number, "can only reply to earlier posts"
                break

    def test_first_post_is_number_one(self, client):
        """Test first post has post_number 1."""
        hot = client.get_hot_topics()
        posts = client.get_topic_posts(hot[0].id)

        first_post = posts[0]
        assert first_post.post_number == 1, "First post should be number 1"


class TestPostListFromTopic:
    """Test posts returned from topic endpoint."""

    def test_posts_list_not_empty(self, client):
        """Test get_topic_posts returns non-empty list."""
        hot = client.get_hot_topics()
        posts = client.get_topic_posts(hot[0].id)

        assert isinstance(posts, list), "Should return list"
        assert len(posts) > 0, "Should have posts"

    def test_all_posts_are_post_objects(self, client):
        """Test all items in posts list are Post objects."""
        hot = client.get_hot_topics()
        posts = client.get_topic_posts(hot[0].id)

        for post in posts:
            assert isinstance(post, Post), "Each item must be Post object"
            assert post.id > 0, "Post id must be positive"
            assert post.post_number >= 1, "post_number must be at least 1"
            assert post.username, "username must not be empty"

    def test_posts_have_content(self, client):
        """Test posts have content fields."""
        hot = client.get_hot_topics()
        posts = client.get_topic_posts(hot[0].id)

        for post in posts:
            assert post.cooked is not None, "cooked must be present"
            assert isinstance(post.cooked, str), "cooked must be string"

    def test_posts_sorted_by_number(self, client):
        """Test posts are sorted by post_number."""
        hot = client.get_hot_topics()
        posts = client.get_topic_posts(hot[0].id)

        if len(posts) > 1:
            for i in range(len(posts) - 1):
                assert posts[i].post_number <= posts[i + 1].post_number, \
                    "Posts should be sorted by post_number"


class TestTopicPagination:
    """Test topic pagination functionality."""

    def test_get_topic_posts_with_post_number(self, client):
        """Test fetching posts starting at specific number."""
        hot = client.get_hot_topics()
        posts = client.get_topic_posts(hot[0].id, post_number=1)

        assert isinstance(posts, list)
        assert len(posts) > 0

    def test_get_all_topic_posts_with_limit(self, client):
        """Test get_all_topic_posts respects max_posts limit."""
        hot = client.get_hot_topics()
        posts = client.get_all_topic_posts(hot[0].id, max_posts=5)

        assert isinstance(posts, list)
        assert len(posts) <= 5

        for post in posts:
            assert isinstance(post, Post)
            assert post.id > 0
            assert post.post_number >= 1
            assert post.username
            assert post.cooked is not None
