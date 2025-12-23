"""Topics API module for fetching topics and posts."""

from __future__ import annotations

from typing import Any

from uscardforum.api.base import BaseAPI
from uscardforum.models.topics import (
    CreatedPost,
    CreatedTopic,
    Post,
    TopicInfo,
    TopicSummary,
)


class TopicsAPI(BaseAPI):
    """API for topic and post operations.

    Handles:
    - Fetching topic lists (hot, new, top)
    - Reading topic metadata
    - Fetching posts from topics
    """

    # -------------------------------------------------------------------------
    # Topic Lists
    # -------------------------------------------------------------------------

    def get_hot_topics(self, *, page: int | None = None) -> list[TopicSummary]:
        """Fetch currently trending topics.

        Args:
            page: Page number for pagination (0-indexed, default: 0)

        Returns:
            List of hot topic summaries
        """
        params: dict[str, Any] = {}
        if page is not None:
            params["page"] = int(page)

        payload = self._get(
            "/hot.json",
            params=params or None,
            headers={"Accept": "application/json, text/plain, */*"},
        )
        topics = payload.get("topic_list", {}).get("topics", [])
        return [TopicSummary(**t) for t in topics]

    def get_new_topics(self, *, page: int | None = None) -> list[TopicSummary]:
        """Fetch latest new topics.

        Args:
            page: Page number for pagination (0-indexed, default: 0)

        Returns:
            List of new topic summaries
        """
        params: dict[str, Any] = {}
        if page is not None:
            params["page"] = int(page)

        payload = self._get(
            "/latest.json",
            params=params or None,
            headers={"Accept": "application/json, text/plain, */*"},
        )
        topics = payload.get("topic_list", {}).get("topics", [])
        return [TopicSummary(**t) for t in topics]

    def get_top_topics(
        self, period: str = "monthly", *, page: int | None = None
    ) -> list[TopicSummary]:
        """Fetch top topics for a time period.

        Args:
            period: One of 'daily', 'weekly', 'monthly', 'quarterly', 'yearly'
            page: Page number for pagination (0-indexed, default: 0)

        Returns:
            List of top topic summaries
        """
        allowed = {"daily", "weekly", "monthly", "quarterly", "yearly"}
        if period not in allowed:
            raise ValueError(f"period must be one of {sorted(allowed)}")

        params: dict[str, Any] = {"period": period}
        if page is not None:
            params["page"] = int(page)

        payload = self._get(
            "/top.json",
            params=params,
            headers={"Accept": "application/json, text/plain, */*"},
        )
        topics = payload.get("topic_list", {}).get("topics", [])
        return [TopicSummary(**t) for t in topics]

    # -------------------------------------------------------------------------
    # Topic Details
    # -------------------------------------------------------------------------

    def get_topic_info(self, topic_id: int) -> TopicInfo:
        """Fetch topic metadata.

        Args:
            topic_id: Topic ID

        Returns:
            Topic info with post count, title, timestamps
        """
        payload = self._get(f"/t/{int(topic_id)}.json")
        return TopicInfo(
            topic_id=topic_id,
            title=payload.get("title"),
            post_count=payload.get("posts_count", 0),
            highest_post_number=payload.get("highest_post_number", 0),
            last_posted_at=payload.get("last_posted_at"),
        )

    # -------------------------------------------------------------------------
    # Posts
    # -------------------------------------------------------------------------

    def get_topic_posts(
        self,
        topic_id: int,
        *,
        post_number: int = 1,
        include_raw: bool = False,
    ) -> list[Post]:
        """Fetch a batch of posts starting at a specific post number.

        Args:
            topic_id: Topic ID
            post_number: Starting post number (default: 1)
            include_raw: Include raw markdown (default: False)

        Returns:
            List of posts sorted by post_number
        """
        params_list: list[tuple[str, Any]] = [
            ("post_number", int(post_number)),
            ("asc", "true"),
            ("include_suggested", "false"),
            ("include_raw", str(include_raw).lower()),
        ]
        payload = self._get(f"t/topic/{int(topic_id)}.json", params=params_list)
        raw_posts = payload.get("post_stream", {}).get("posts", [])

        posts = []
        for p in raw_posts:
            post = Post(
                id=p.get("id", 0),
                post_number=p.get("post_number", 0),
                username=p.get("username", ""),
                cooked=p.get("cooked"),
                raw=p.get("raw") if include_raw else None,
                created_at=p.get("created_at"),
                updated_at=p.get("updated_at"),
                like_count=p.get("like_count", 0),
                reply_count=p.get("reply_count", 0),
                reply_to_post_number=p.get("reply_to_post_number"),
            )
            posts.append(post)

        posts.sort(key=lambda p: p.post_number)
        return posts

    def get_all_topic_posts(
        self,
        topic_id: int,
        *,
        include_raw: bool = False,
        start_post_number: int = 1,
        end_post_number: int | None = None,
        max_posts: int | None = None,
    ) -> list[Post]:
        """Fetch all posts in a topic with automatic pagination.

        Args:
            topic_id: Topic ID
            include_raw: Include raw markdown (default: False)
            start_post_number: Starting post number (default: 1)
            end_post_number: Optional ending post number
            max_posts: Optional maximum posts to fetch

        Returns:
            List of all matching posts
        """
        current = max(1, int(start_post_number))
        collected: list[Post] = []
        seen_numbers: set[int] = set()

        while True:
            if max_posts is not None and len(collected) >= int(max_posts):
                break

            batch = self.get_topic_posts(
                topic_id, post_number=current, include_raw=include_raw
            )
            if not batch:
                break

            last_in_batch: int | None = None
            for post in batch:
                pn = post.post_number
                if pn not in seen_numbers:
                    if end_post_number is not None and pn > int(end_post_number):
                        last_in_batch = last_in_batch or pn
                        continue
                    seen_numbers.add(pn)
                    collected.append(post)
                    last_in_batch = pn
                    if max_posts is not None and len(collected) >= int(max_posts):
                        break

            if last_in_batch is None:
                break
            current = last_in_batch + 1
            if end_post_number is not None and current > int(end_post_number):
                break

        collected.sort(key=lambda p: p.post_number)
        return collected

    # -------------------------------------------------------------------------
    # Creating Topics & Posts (requires authentication)
    # -------------------------------------------------------------------------

    def create_topic(
        self,
        title: str,
        raw: str,
        category_id: int | None = None,
        tags: list[str] | None = None,
        csrf_token: str | None = None,
    ) -> CreatedTopic:
        """Create a new topic.

        Args:
            title: Topic title
            raw: Post content in markdown
            category_id: Optional category ID
            tags: Optional list of tags
            csrf_token: CSRF token (required for authenticated requests)

        Returns:
            Created topic info with topic_id, slug, and post_id
        """
        json_data: dict[str, Any] = {
            "title": title,
            "raw": raw,
        }
        if category_id is not None:
            json_data["category"] = int(category_id)
        if tags:
            json_data["tags"] = tags

        headers = {
            "Accept": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{self._base_url}/",
        }
        if csrf_token:
            headers["X-CSRF-Token"] = csrf_token

        payload = self._post("/posts.json", json=json_data, headers=headers)
        return CreatedTopic.from_api_response(payload)

    def create_post(
        self,
        topic_id: int,
        raw: str,
        reply_to_post_number: int | None = None,
        csrf_token: str | None = None,
    ) -> CreatedPost:
        """Create a new post/reply in an existing topic.

        Args:
            topic_id: Topic ID to reply to
            raw: Post content in markdown
            reply_to_post_number: Optional post number to reply to
            csrf_token: CSRF token (required for authenticated requests)

        Returns:
            Created post info with post_id, post_number, etc.
        """
        json_data: dict[str, Any] = {
            "topic_id": int(topic_id),
            "raw": raw,
        }
        if reply_to_post_number is not None:
            json_data["reply_to_post_number"] = int(reply_to_post_number)

        headers = {
            "Accept": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{self._base_url}/t/{int(topic_id)}",
        }
        if csrf_token:
            headers["X-CSRF-Token"] = csrf_token

        payload = self._post("/posts.json", json=json_data, headers=headers)
        return CreatedPost.from_api_response(payload)

