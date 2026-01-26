"""
Agent管理器

职责：
- 管理所有陪审员Agent实例
- 提供统一的对话接口
- 处理投票结算
"""

from backend.agents.juror_agent import JurorAgent


class AgentManager:
    """
    管理多个陪审员Agent

    单例模式，整个游戏生命周期只有一个实例。
    """

    def __init__(self, juror_ids: list[str] = None):
        """
        初始化Agent管理器

        Args:
            juror_ids: 要加载的陪审员ID列表，None则加载全部
        """
        self.agents: dict[str, JurorAgent] = {}
        self.juror_ids = juror_ids or []

    def load_all_jurors(self, content_path: str = "content/jurors") -> None:
        """
        加载所有陪审员Agent

        Args:
            content_path: 角色卡目录

        TODO:
        - 如果juror_ids为空，扫描目录获取所有JSON文件
        - 为每个juror_id创建JurorAgent实例
        - 存入self.agents字典
        """
        pass

    def get_juror(self, juror_id: str) -> JurorAgent:
        """
        获取指定陪审员Agent

        Args:
            juror_id: 陪审员ID

        Returns:
            JurorAgent实例

        Raises:
            KeyError: 陪审员不存在

        TODO:
        - 从self.agents获取
        - 不存在则抛出异常
        """
        pass

    async def chat_with_juror(self, juror_id: str, message: str) -> dict:
        """
        与指定陪审员对话

        Args:
            juror_id: 陪审员ID
            message: 玩家消息

        Returns:
            {
                "reply": str,
                "juror_id": str
            }

        TODO:
        - 获取agent
        - 调用agent.chat()
        - 返回结果
        """
        pass

    def get_all_juror_info(self) -> list[dict]:
        """
        获取所有陪审员的基本信息（用于前端显示）

        Returns:
            [
                {"id": str, "name": str, "first_message": str},
                ...
            ]

        TODO:
        - 遍历self.agents
        - 提取基本信息（不含隐藏数据）
        """
        pass

    def collect_votes(self) -> dict:
        """
        收集所有陪审员的投票

        Returns:
            {
                "votes": {
                    "juror_id": {"name": str, "vote": "GUILTY"|"NOT_GUILTY"},
                    ...
                },
                "guilty_count": int,
                "not_guilty_count": int,
                "verdict": "GUILTY"|"NOT_GUILTY"
            }

        TODO:
        - 遍历agents，调用get_final_vote()
        - 统计票数
        - 计算最终判决
        """
        pass

    def reset_all(self) -> None:
        """
        重置所有Agent（新游戏）

        TODO:
        - 遍历agents，调用reset()
        """
        pass
