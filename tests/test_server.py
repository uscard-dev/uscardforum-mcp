"""
Integration tests for MCP Server tools and prompts.

Tests the FastMCP server tools against the actual USCardForum API.
"""

import pytest


class TestServerPrompts:
    """Tests for server prompts (Chinese)."""

    def test_research_topic_prompt(self):
        """Test research_topic prompt generation (Chinese)."""
        from uscardforum.server import research_topic

        result = research_topic("Chase Sapphire Reserve")

        assert "Chase Sapphire Reserve" in result
        assert "search_forum" in result
        assert "数据点" in result  # Chinese for "data points"
        assert "中文" in result  # Should mention Chinese output

    def test_analyze_user_prompt(self):
        """Test analyze_user prompt generation (Chinese)."""
        from uscardforum.server import analyze_user

        result = analyze_user("creditexpert")

        assert "creditexpert" in result
        assert "用户" in result  # Chinese for "user"
        assert "徽章" in result  # Chinese for "badges"
        assert "中文" in result  # Should mention Chinese output

    def test_find_data_points_prompt(self):
        """Test find_data_points prompt generation (Chinese)."""
        from uscardforum.server import find_data_points

        result = find_data_points("Chase 5/24 rule")

        assert "Chase 5/24 rule" in result
        assert "数据点" in result  # Chinese for "data points"
        assert "中文" in result  # Should mention Chinese output

    def test_compare_cards_prompt(self):
        """Test compare_cards prompt generation (Chinese)."""
        from uscardforum.server import compare_cards

        result = compare_cards("Chase Sapphire Reserve", "Amex Platinum")

        assert "Chase Sapphire Reserve" in result
        assert "Amex Platinum" in result
        assert "比较" in result  # Chinese for "compare"
        assert "中文" in result  # Should mention Chinese output


class TestServerInstructions:
    """Tests for server instructions."""

    def test_server_instructions_in_chinese(self):
        """Test that server instructions are in Chinese."""
        from uscardforum.server import SERVER_INSTRUCTIONS

        assert "中文" in SERVER_INSTRUCTIONS
        assert "USCardForum MCP 服务器" in SERVER_INSTRUCTIONS
        assert "核心概念" in SERVER_INSTRUCTIONS
        assert "最佳实践" in SERVER_INSTRUCTIONS


class TestStaticTokenVerifier:
    """Tests for StaticTokenVerifier."""

    def test_verify_token_valid(self):
        """Test that valid token returns AccessToken."""
        import asyncio

        from uscardforum.server_core import StaticTokenVerifier

        verifier = StaticTokenVerifier("my-secret-token")
        result = asyncio.run(verifier.verify_token("my-secret-token"))

        assert result is not None
        assert result.token == "my-secret-token"
        assert result.client_id == "nitan-user"
        assert "read" in result.scopes
        assert "write" in result.scopes

    def test_verify_token_invalid(self):
        """Test that invalid token returns None."""
        import asyncio

        from uscardforum.server_core import StaticTokenVerifier

        verifier = StaticTokenVerifier("my-secret-token")
        result = asyncio.run(verifier.verify_token("wrong-token"))

        assert result is None

    def test_verify_token_empty(self):
        """Test that empty token returns None."""
        import asyncio

        from uscardforum.server_core import StaticTokenVerifier

        verifier = StaticTokenVerifier("my-secret-token")
        result = asyncio.run(verifier.verify_token(""))

        assert result is None
