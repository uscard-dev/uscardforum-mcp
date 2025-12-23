"""Core MCP server configuration and shared helpers."""
from __future__ import annotations

import os
from typing import Literal

from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.server import AuthSettings

from uscardforum.client import DiscourseClient


class StaticTokenVerifier(TokenVerifier):
    """Token verifier that checks against a static token from environment."""

    def __init__(self, expected_token: str) -> None:
        self._expected_token = expected_token

    async def verify_token(self, token: str) -> AccessToken | None:
        """Verify a bearer token against the expected NITAN_TOKEN."""
        if token == self._expected_token:
            return AccessToken(
                token=token,
                client_id="nitan-user",
                scopes=["read", "write"],
            )
        return None

# =============================================================================
# Server Configuration
# =============================================================================

# Transport mode: stdio (default), sse, or streamable-http
MCP_TRANSPORT: Literal["stdio", "sse", "streamable-http"] = os.environ.get(
    "MCP_TRANSPORT", "stdio"
)  # type: ignore[assignment]

# HTTP server settings (only used for sse/streamable-http transports)
MCP_HOST = os.environ.get("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.environ.get("MCP_PORT", "8000"))

SERVER_INSTRUCTIONS = """
# USCardForum MCP 服务器

你已连接到 USCardForum Discourse API，这是一个专注于美国信用卡、积分、里程和财务优化策略的社区。

**重要：请使用中文回复所有问题。**

## 核心概念

### 主题与帖子
- **主题 (Topic)**：包含标题和多个帖子的讨论串
- **帖子 (Post)**：主题中的单条消息（post_number 从 1 开始）
- **主题 ID**：主题的数字标识符（在 URL 中如 /t/topic-slug/12345）

### 分类
USCardForum 的主要分类包括：
- 信用卡（申请、批准、策略）
- 银行账户（开户奖励、要求）
- 旅行（积分兑换、行程报告）
- 数据点（社区分享的经验）

### 用户
- 每个用户有唯一的用户名
- 用户通过参与获得徽章
- 用户可以互相关注

## 最佳实践

1. **发现内容**
   - 使用 `get_hot_topics` 或 `get_new_topics` 查看当前讨论
   - 使用 `search_forum` 配合关键词查找特定内容

2. **阅读主题**
   - 首先使用 `get_topic_info` 检查帖子数量
   - 超过 100 帖的主题，使用 `get_all_topic_posts` 并设置 `max_posts` 限制
   - 分批处理大型主题，避免响应过长

3. **用户研究**
   - 使用 `get_user_summary` 获取用户活动概览
   - 使用 `get_user_topics` 查看用户发起的讨论
   - 使用 `get_user_replies` 查看用户的回复贡献

4. **搜索技巧**
   - Discourse 支持操作符：`in:title`、`category:`、`@username`、`#tag`
   - 排序选项：relevance、latest、views、likes、activity
   - 示例："Chase Sapphire in:title order:latest"

5. **身份验证**
   - 仅以下功能需要登录：通知、书签、订阅
   - 自动登录：设置 NITAN_USERNAME 和 NITAN_PASSWORD 环境变量
   - 手动登录：如未使用自动登录，调用 `login`
   - 使用 `get_current_session` 检查登录状态

## 回复格式要求

展示论坛内容时：
- 总结长帖内容，而非完整引用
- 包含相关元数据（作者、日期、点赞数）
- 引用具体的帖子编号作为来源
- 突出显示可操作的数据点
- **始终使用中文回复**
"""

# Token for streamable-http authentication (optional)
NITAN_TOKEN = os.environ.get("NITAN_TOKEN")

# Create token verifier and auth settings if NITAN_TOKEN is set and using streamable-http
_token_verifier: TokenVerifier | None = None
_auth_settings: AuthSettings | None = None
if NITAN_TOKEN and MCP_TRANSPORT == "streamable-http":
    _token_verifier = StaticTokenVerifier(NITAN_TOKEN)
    # AuthSettings required when using token_verifier
    # issuer_url is a placeholder since we use static token verification
    _auth_settings = AuthSettings(
        issuer_url="https://uscardforum.com/oauth",  # type: ignore[arg-type]
        resource_server_url=f"http://{MCP_HOST}:{MCP_PORT}",  # type: ignore[arg-type]
    )

# Initialize FastMCP server with instructions and HTTP settings
mcp = FastMCP(
    name="uscardforum",
    instructions=SERVER_INSTRUCTIONS,
    host=MCP_HOST,
    port=MCP_PORT,
    token_verifier=_token_verifier,
    auth=_auth_settings,
)

# Global client instance
_client: DiscourseClient | None = None
_login_attempted: bool = False


def get_client() -> DiscourseClient:
    """Get or create the Discourse client instance."""
    global _client, _login_attempted

    if _client is None:
        base_url = os.environ.get("USCARDFORUM_URL", "https://www.uscardforum.com")
        timeout = float(os.environ.get("USCARDFORUM_TIMEOUT", "15.0"))

        username = os.environ.get("NITAN_USERNAME")
        password = os.environ.get("NITAN_PASSWORD")
        user_api_key = os.environ.get("NITAN_API_KEY")
        user_api_client_id = os.environ.get("NITAN_API_CLIENT_ID")

        _client = DiscourseClient(
            base_url=base_url,
            timeout_seconds=timeout,
            user_api_key=user_api_key if not (username and password) else None,
            user_api_client_id=(
                user_api_client_id if not (username and password) else None
            ),
        )

        if _client.is_authenticated:
            print("[uscardforum] Using User API Key authentication")
        elif not _login_attempted:
            _login_attempted = True

            if username and password:
                try:
                    result = _client.login(username, password)
                    if result.success:
                        print(f"[uscardforum] Auto-login successful as '{result.username}'")
                    elif result.requires_2fa:
                        print(
                            "[uscardforum] Auto-login failed: 2FA required. Use login() tool with second_factor_token."
                        )
                    else:
                        print(
                            f"[uscardforum] Auto-login failed: {result.error or 'Unknown error'}"
                        )
                except Exception as e:  # pragma: no cover - logging side effect
                    print(f"[uscardforum] Auto-login error: {e}")

    return _client


def main() -> None:
    """Run the MCP server with configured transport."""
    if MCP_TRANSPORT in ("sse", "streamable-http"):
        print(f"[uscardforum] Starting MCP server on http://{MCP_HOST}:{MCP_PORT}")
        print(f"[uscardforum] Transport: {MCP_TRANSPORT}")
        if NITAN_TOKEN and MCP_TRANSPORT == "streamable-http":
            print("[uscardforum] Authentication: Bearer token required (NITAN_TOKEN)")

    # Initialize client and perform auto-login before starting the server
    get_client()

    mcp.run(transport=MCP_TRANSPORT)


__all__ = [
    "mcp",
    "MCP_HOST",
    "MCP_PORT",
    "MCP_TRANSPORT",
    "NITAN_TOKEN",
    "SERVER_INSTRUCTIONS",
    "get_client",
    "main",
]

