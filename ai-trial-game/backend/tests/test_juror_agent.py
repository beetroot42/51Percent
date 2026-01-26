"""
JurorAgent测试
"""
import pytest
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.juror_agent import JurorAgent, JurorConfig

# 测试用角色卡路径
CONTENT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "content/jurors"
)


class TestJurorAgentConfig:
    """Task 3.1: 配置加载测试"""

    def test_load_config(self):
        """测试加载角色卡"""
        agent = JurorAgent("test_juror", content_path=CONTENT_PATH)

        assert agent.config is not None
        assert isinstance(agent.config, JurorConfig)

    def test_config_has_required_fields(self):
        """测试配置包含必要字段"""
        agent = JurorAgent("test_juror", content_path=CONTENT_PATH)

        assert agent.config.id == "test_juror"
        assert agent.config.name is not None
        assert agent.config.topic_weights is not None

    def test_initial_stance(self):
        """测试初始立场值"""
        agent = JurorAgent("test_juror", content_path=CONTENT_PATH)

        assert agent.stance_value == agent.config.initial_stance

    def test_get_first_message(self):
        """测试获取开场白"""
        agent = JurorAgent("test_juror", content_path=CONTENT_PATH)

        msg = agent.get_first_message()
        assert msg is not None
        assert len(msg) > 0


class TestJurorAgentPrompt:
    """Task 3.2: Prompt构建测试"""

    def test_build_system_prompt(self):
        """测试构建system prompt"""
        agent = JurorAgent("test_juror", content_path=CONTENT_PATH)

        prompt = agent._build_system_prompt()

        assert prompt is not None
        assert len(prompt) > 0
        assert agent.config.name in prompt

    def test_get_stance_description(self):
        """测试立场描述"""
        agent = JurorAgent("test_juror", content_path=CONTENT_PATH)

        # 测试不同立场值
        agent.stance_value = -60
        desc = agent._get_stance_description()
        assert "有罪" in desc or "guilty" in desc.lower()

        agent.stance_value = 60
        desc = agent._get_stance_description()
        assert "无罪" in desc or "not guilty" in desc.lower()


class TestJurorAgentStance:
    """Task 3.4: 立场追踪测试"""

    def test_update_stance_positive(self):
        """测试正向话题偏移"""
        agent = JurorAgent("test_juror", content_path=CONTENT_PATH)

        initial = agent.stance_value
        weight = agent.config.topic_weights.get("技术责任", 0)

        agent._update_stance(["技术责任"], "positive")

        if weight != 0:
            assert agent.stance_value != initial

    def test_update_stance_negative(self):
        """测试负向话题偏移"""
        agent = JurorAgent("test_juror", content_path=CONTENT_PATH)

        initial = agent.stance_value
        agent._update_stance(["情感诉求"], "positive")

        # 如果情感诉求权重为负，立场应下降
        weight = agent.config.topic_weights.get("情感诉求", 0)
        if weight < 0:
            assert agent.stance_value < initial

    def test_stance_clamped(self):
        """测试立场值限制在[-100, 100]"""
        agent = JurorAgent("test_juror", content_path=CONTENT_PATH)

        agent.stance_value = 95
        agent._update_stance(["技术责任"] * 10, "positive")
        assert agent.stance_value <= 100

        agent.stance_value = -95
        agent._update_stance(["情感诉求"] * 10, "positive")
        assert agent.stance_value >= -100

    def test_get_final_vote_positive(self):
        """测试最终投票 - 无罪"""
        agent = JurorAgent("test_juror", content_path=CONTENT_PATH)
        agent.stance_value = 50

        assert agent.get_final_vote() == True  # True = 无罪

    def test_get_final_vote_negative(self):
        """测试最终投票 - 有罪"""
        agent = JurorAgent("test_juror", content_path=CONTENT_PATH)
        agent.stance_value = -50

        assert agent.get_final_vote() == False  # False = 有罪


class TestJurorAgentChat:
    """Task 3.3: 对话测试（需要API Key）"""

    @pytest.mark.skip(reason="需要API Key，手动运行")
    def test_chat_integration(self):
        """集成测试：实际调用LLM"""
        agent = JurorAgent("test_juror", content_path=CONTENT_PATH)

        result = asyncio.run(agent.chat("你好"))

        assert "reply" in result
        assert len(result["reply"]) > 0
        print(f"Agent回复: {result['reply']}")

    @pytest.mark.skip(reason="需要API Key，手动运行")
    def test_conversation_history(self):
        """测试对话历史记录"""
        agent = JurorAgent("test_juror", content_path=CONTENT_PATH)

        asyncio.run(agent.chat("你好"))
        asyncio.run(agent.chat("你怎么看这个案件？"))

        assert len(agent.conversation_history) == 2


class TestJurorAgentReset:
    """重置测试"""

    def test_reset(self):
        """测试重置状态"""
        agent = JurorAgent("test_juror", content_path=CONTENT_PATH)

        agent.stance_value = 50
        agent.conversation_history.append({"player": "test", "juror": "test"})

        agent.reset()

        assert agent.stance_value == agent.config.initial_stance
        assert len(agent.conversation_history) == 0
