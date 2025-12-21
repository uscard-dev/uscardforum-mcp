"""MCP prompt generators."""
from __future__ import annotations

from uscardforum.server_core import mcp


@mcp.prompt()
def research_topic(topic_query: str) -> str:
    """
    生成一个用于研究论坛特定主题的提示。

    Args:
        topic_query: 要研究的内容（例如 "Chase Sapphire Reserve 权益"）
    """
    return f"""我需要在 USCardForum 上研究"{topic_query}"。

请帮我：
1. 使用 search_forum 搜索相关讨论
2. 找到最有帮助的主题（关注点赞数高和回复多的帖子）
3. 阅读最佳主题中的关键帖子
4. 总结社区共识和数据点

重点关注：
- 近期信息（尽可能在过去 6 个月内）
- 高互动帖子（点赞、回复多）
- 用户真实经验的数据点
- 任何官方公告或政策变化

请用中文以结构化格式呈现发现，并标注来源（主题 ID 和帖子编号）。"""


@mcp.prompt()
def analyze_user(username: str) -> str:
    """
    生成一个用于分析论坛用户资料和贡献的提示。

    Args:
        username: 要分析的用户名
    """
    return f"""我想分析论坛用户"{username}"。

请：
1. 获取用户概要了解基本情况
2. 查看他们最近的主题和回复
3. 检查他们的徽章和认可

总结以下内容：
- 在论坛的活跃程度
- 最擅长的话题领域
- 贡献质量（有用性、准确性）
- 在社区的地位（粉丝数、徽章）

请用中文回复，帮助评估该用户建议和数据点的可信度。"""


@mcp.prompt()
def find_data_points(subject: str) -> str:
    """
    生成一个用于查找用户报告数据点的提示。

    Args:
        subject: 要查找数据点的主题（例如 "Chase 5/24 规则"）
    """
    return f"""我需要查找关于"{subject}"的社区数据点。

请：
1. 搜索提及"{subject}"的讨论
2. 查找用户分享个人经历的帖子
3. 重点关注近期数据点（过去 3-6 个月）

对于每个相关数据点，提取：
- 发生了什么（批准、拒绝、奖励等）
- 相关细节（日期、金额、情况）
- 用户的情况（如有提及）
- 帖子来源（主题 ID 和帖子编号）

请用中文汇总，展示数据中的规律和趋势。"""


@mcp.prompt()
def compare_cards(card1: str, card2: str) -> str:
    """
    生成一个用于比较两张信用卡讨论的提示。

    Args:
        card1: 第一张卡名称（例如 "Chase Sapphire Reserve"）
        card2: 第二张卡名称（例如 "Amex Platinum"）
    """
    return f"""请帮我比较"{card1}"和"{card2}"在论坛上的讨论。

请：
1. 分别搜索两张卡的讨论
2. 找出每张卡的优缺点（根据社区反馈）
3. 比较关键方面：
   - 开卡奖励和要求
   - 年费和权益
   - 积分价值和使用
   - 社区推荐程度

最后用中文总结：
- 各卡适合什么类型的用户
- 社区更推荐哪张卡及原因
- 需要注意的申请策略"""


__all__ = [
    "research_topic",
    "analyze_user",
    "find_data_points",
    "compare_cards",
]

