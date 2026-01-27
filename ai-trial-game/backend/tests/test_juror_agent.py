"""
JurorAgent tests.
"""
import pytest
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.juror_agent import JurorAgent, JurorConfig

# Test character card path
CONTENT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "content/jurors"
)


class TestJurorAgentConfig:
    """Task 3.1: Config loading tests."""

    def test_load_config(self):
        """Test loading character card."""
        agent = JurorAgent("test_juror", content_path=CONTENT_PATH)

        assert agent.config is not None
        assert isinstance(agent.config, JurorConfig)

    def test_config_has_required_fields(self):
        """Test required fields exist."""
        agent = JurorAgent("test_juror", content_path=CONTENT_PATH)

        assert agent.config.id == "test_juror"
        assert agent.config.name is not None
        assert agent.config.topic_weights is not None

    def test_initial_stance(self):
        """Test initial stance value."""
        agent = JurorAgent("test_juror", content_path=CONTENT_PATH)

        assert agent.stance_value == agent.config.initial_stance

    def test_get_first_message(self):
        """Test first message."""
        agent = JurorAgent("test_juror", content_path=CONTENT_PATH)

        msg = agent.get_first_message()
        assert msg is not None
        assert len(msg) > 0


class TestJurorAgentPrompt:
    """Task 3.2: Prompt build tests."""

    def test_build_system_prompt(self):
        """Test building system prompt."""
        agent = JurorAgent("test_juror", content_path=CONTENT_PATH)

        prompt = agent._build_system_prompt()

        assert prompt is not None
        assert len(prompt) > 0
        assert agent.config.name in prompt

    def test_get_stance_description(self):
        """Test stance description."""
        agent = JurorAgent("test_juror", content_path=CONTENT_PATH)

        # Test different stance values
        agent.stance_value = -60
        desc = agent._get_stance_description()
        assert "guilty" in desc.lower()

        agent.stance_value = 60
        desc = agent._get_stance_description()
        assert "not guilty" in desc.lower()


class TestJurorAgentStance:
    """Task 3.4: Stance tracking tests."""

    def test_update_stance_positive(self):
        """Test positive topic shift."""
        agent = JurorAgent("test_juror", content_path=CONTENT_PATH)

        initial = agent.stance_value
        weight = agent.config.topic_weights.get("技术责任", 0)

        agent._update_stance(["技术责任"], "positive")

        if weight != 0:
            assert agent.stance_value != initial

    def test_update_stance_negative(self):
        """Test negative topic shift."""
        agent = JurorAgent("test_juror", content_path=CONTENT_PATH)

        initial = agent.stance_value
        agent._update_stance(["情感诉求"], "positive")

        # If emotional appeal weight is negative, stance should decrease
        weight = agent.config.topic_weights.get("情感诉求", 0)
        if weight < 0:
            assert agent.stance_value < initial

    def test_stance_clamped(self):
        """Test stance clamping to [-100, 100]."""
        agent = JurorAgent("test_juror", content_path=CONTENT_PATH)

        agent.stance_value = 95
        agent._update_stance(["技术责任"] * 10, "positive")
        assert agent.stance_value <= 100

        agent.stance_value = -95
        agent._update_stance(["情感诉求"] * 10, "positive")
        assert agent.stance_value >= -100

    def test_get_final_vote_positive(self):
        """Test final vote - not guilty."""
        agent = JurorAgent("test_juror", content_path=CONTENT_PATH)
        agent.stance_value = 50

        assert agent.get_final_vote() is True  # True = not guilty

    def test_get_final_vote_negative(self):
        """Test final vote - guilty."""
        agent = JurorAgent("test_juror", content_path=CONTENT_PATH)
        agent.stance_value = -50

        assert agent.get_final_vote() is False  # False = guilty


class TestJurorAgentChat:
    """Task 3.3: Chat tests (requires API key)."""

    @pytest.mark.skip(reason="Requires API key; run manually")
    def test_chat_integration(self):
        """Integration test: call LLM."""
        agent = JurorAgent("test_juror", content_path=CONTENT_PATH)

        result = asyncio.run(agent.chat("Hello"))

        assert "reply" in result
        assert len(result["reply"]) > 0
        print(f"Agent reply: {result['reply']}")

    @pytest.mark.skip(reason="Requires API key; run manually")
    def test_conversation_history(self):
        """Test conversation history."""
        agent = JurorAgent("test_juror", content_path=CONTENT_PATH)

        asyncio.run(agent.chat("Hello"))
        asyncio.run(agent.chat("What do you think about this case?"))

        assert len(agent.conversation_history) == 2


class TestJurorAgentReset:
    """Reset tests."""

    def test_reset(self):
        """Test reset state."""
        agent = JurorAgent("test_juror", content_path=CONTENT_PATH)

        agent.stance_value = 50
        agent.conversation_history.append({"player": "test", "juror": "test"})

        agent.reset()

        assert agent.stance_value == agent.config.initial_stance
        assert len(agent.conversation_history) == 0
