"""
陪审员Agent模块

职责：
- 加载陪审员角色卡
- 管理对话历史
- 调用LLM生成角色扮演回复
- 追踪隐藏立场值
- 解析话题并计算偏移
"""

import json
import re
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class JurorConfig:
    """陪审员配置（从JSON加载）"""
    id: str
    name: str
    background: str
    personality: list[str]
    speaking_style: str
    initial_stance: int
    topic_weights: dict[str, int]
    first_message: str


@dataclass
class ConversationTurn:
    """单轮对话"""
    player: str
    juror: str


class JurorAgent:
    """
    陪审员Agent

    使用spoon-core的ReAct模式，但主要用于角色扮演对话。
    立场追踪完全隐藏，玩家只看到自然对话。
    """

    def __init__(self, juror_id: str, content_path: str = "content/jurors"):
        """
        初始化陪审员Agent

        Args:
            juror_id: 陪审员ID，对应JSON文件名
            content_path: 角色卡目录路径
        """
        self.juror_id = juror_id
        self.config: JurorConfig = None
        self.stance_value: int = 0
        self.conversation_history: list[ConversationTurn] = []
        self.llm_client = None  # TODO: 初始化Claude客户端

        self._load_config(content_path)
        self._init_llm()

    def _load_config(self, content_path: str) -> None:
        """
        从JSON文件加载角色卡配置

        Args:
            content_path: 角色卡目录路径

        TODO:
        - 读取 {content_path}/{juror_id}.json
        - 解析为JurorConfig
        - 设置initial_stance
        """
        pass

    def _init_llm(self) -> None:
        """
        初始化LLM客户端

        TODO:
        - 使用spoon-core的LLM抽象
        - 或直接使用anthropic SDK
        - 配置model、temperature等参数
        """
        pass

    def _build_system_prompt(self) -> str:
        """
        构建角色扮演的system prompt

        Returns:
            完整的system prompt字符串

        TODO:
        - 组合角色背景、性格、说话风格
        - 注入案件背景
        - 添加立场描述（根据当前stance_value）
        - 添加话题分析指令（输出隐藏标记）
        """
        pass

    def _get_stance_description(self) -> str:
        """
        根据当前立场值生成描述

        Returns:
            立场描述字符串，用于system prompt

        TODO:
        - stance < -50: "强烈倾向有罪"
        - stance < -20: "倾向有罪"
        - stance < 20: "中立"
        - stance < 50: "倾向无罪"
        - stance >= 50: "强烈倾向无罪"
        """
        pass

    async def chat(self, player_message: str) -> dict:
        """
        与玩家进行一轮对话

        Args:
            player_message: 玩家输入

        Returns:
            {
                "reply": str,      # 陪审员回复（纯自然对话）
                "juror_id": str    # 陪审员ID
            }

        TODO:
        - 构建完整prompt（system + history + user message）
        - 调用LLM
        - 解析回复中的话题标记
        - 更新立场值
        - 清理回复（移除标记）
        - 记录对话历史
        - 返回结果
        """
        pass

    def _parse_topics(self, response: str) -> tuple[list[str], str]:
        """
        从Agent回复中解析话题标记

        Args:
            response: LLM原始回复

        Returns:
            (topics: list[str], impact: str)
            - topics: 识别到的话题列表
            - impact: "positive" / "negative" / "neutral"

        TODO:
        - 使用正则匹配 <!-- TOPICS: {...} -->
        - 解析JSON
        - 返回话题和影响
        """
        pass

    def _update_stance(self, topics: list[str], impact: str) -> None:
        """
        根据话题更新隐藏立场值

        Args:
            topics: 本轮对话涉及的话题
            impact: 话题的影响方向

        TODO:
        - 遍历topics
        - 查找topic_weights
        - 根据impact调整权重
        - 累加到stance_value
        - 限制在[-100, 100]范围
        """
        pass

    def _clean_reply(self, response: str) -> str:
        """
        清理回复，移除隐藏标记

        Args:
            response: LLM原始回复

        Returns:
            清理后的纯对话文本

        TODO:
        - 移除 <!-- TOPICS: ... -->
        - 移除其他可能的标记
        - strip空白
        """
        pass

    def get_final_vote(self) -> bool:
        """
        获取最终投票

        Returns:
            True = 无罪, False = 有罪

        TODO:
        - return self.stance_value > 0
        """
        pass

    def get_first_message(self) -> str:
        """
        获取陪审员的开场白

        Returns:
            first_message字符串
        """
        pass

    def reset(self) -> None:
        """
        重置Agent状态（用于新游戏）

        TODO:
        - 清空conversation_history
        - 重置stance_value为initial_stance
        """
        pass
