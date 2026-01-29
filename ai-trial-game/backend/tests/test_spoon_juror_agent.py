"""
SpoonJurorAgent tests (unit only, spoon-core mocked).
"""
import asyncio
import importlib
import sys
import types
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).parent.parent))

CONTENT_PATH = str(Path(__file__).parent.parent.parent / "content" / "jurors")


def _install_spoon_ai_stubs(monkeypatch):
    """Install spoon-core stubs for isolated testing."""
    spoon_ai = types.ModuleType("spoon_ai")
    agents = types.ModuleType("spoon_ai.agents")
    toolcall = types.ModuleType("spoon_ai.agents.toolcall")
    chat = types.ModuleType("spoon_ai.chat")
    tools = types.ModuleType("spoon_ai.tools")
    schema = types.ModuleType("spoon_ai.schema")
    tools_base = types.ModuleType("spoon_ai.tools.base")

    class Memory:
        def __init__(self):
            self.messages = []

        def clear(self):
            self.messages = []

    class ChatBot:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.reply_text = kwargs.get("reply_text")

        async def ask(self, messages, system_msg):
            if self.reply_text is not None:
                return self.reply_text
            return "Default reply. <!-- ANALYSIS: {\"topics\": [], \"impact\": \"neutral\"} -->"

    class ToolManager:
        def __init__(self, tools_list):
            self.tools = tools_list

    class AgentState:
        IDLE = "IDLE"

    class ToolChoice:
        NONE = "none"
        AUTO = "auto"

    class ToolCallAgent:
        def __init__(self, name, description, system_prompt, llm, memory, available_tools, **kwargs):
            self.name = name
            self.description = description
            self.system_prompt = system_prompt
            self.llm = llm
            self.memory = memory
            self.available_tools = available_tools
            self.state = AgentState.IDLE
            self.current_step = 0

        async def add_message(self, role, content):
            self.memory.messages.append({"role": role, "content": content})

    class BaseTool:
        name = ""
        description = ""
        parameters = {}

        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

        def to_param(self):
            return {
                "type": "function",
                "function": {
                    "name": self.name,
                    "description": self.description,
                    "parameters": self.parameters,
                },
            }

    class ToolFailure(Exception):
        def __init__(self, message, cause=None):
            super().__init__(message)
            self.cause = cause

    toolcall.ToolCallAgent = ToolCallAgent
    chat.ChatBot = ChatBot
    chat.Memory = Memory
    tools.ToolManager = ToolManager
    schema.AgentState = AgentState
    schema.ToolChoice = ToolChoice
    tools_base.BaseTool = BaseTool
    tools_base.ToolFailure = ToolFailure

    spoon_ai.agents = agents
    spoon_ai.chat = chat
    spoon_ai.tools = tools
    spoon_ai.schema = schema

    monkeypatch.setitem(sys.modules, "spoon_ai", spoon_ai)
    monkeypatch.setitem(sys.modules, "spoon_ai.agents", agents)
    monkeypatch.setitem(sys.modules, "spoon_ai.agents.toolcall", toolcall)
    monkeypatch.setitem(sys.modules, "spoon_ai.chat", chat)
    monkeypatch.setitem(sys.modules, "spoon_ai.tools", tools)
    monkeypatch.setitem(sys.modules, "spoon_ai.schema", schema)
    monkeypatch.setitem(sys.modules, "spoon_ai.tools.base", tools_base)


def _import_spoon_juror_agent(monkeypatch):
    """Import SpoonJurorAgent with mocked spoon-core."""
    _install_spoon_ai_stubs(monkeypatch)
    if "agents.spoon_juror_agent" in sys.modules:
        del sys.modules["agents.spoon_juror_agent"]
    return importlib.import_module("agents.spoon_juror_agent")


class FakeChatBot:
    """Fake ChatBot for testing without LLM API."""
    def __init__(self, reply_text):
        self.reply_text = reply_text

    async def ask(self, messages, system_msg):
        return self.reply_text


class TestSpoonJurorAgentConfig:
    """Configuration loading tests."""

    def test_load_config_success(self, monkeypatch):
        """Test loading juror config from JSON."""
        module = _import_spoon_juror_agent(monkeypatch)
        config = module.SpoonJurorAgent._load_juror_config("test_juror", CONTENT_PATH)
        assert config.id == "test_juror"
        assert config.name is not None

    def test_load_config_missing_file(self, monkeypatch):
        """Test loading non-existent config raises error."""
        module = _import_spoon_juror_agent(monkeypatch)
        with pytest.raises(FileNotFoundError):
            module.SpoonJurorAgent._load_juror_config("missing_juror", CONTENT_PATH)

    def test_initial_stance_matches_config(self, monkeypatch):
        """Test initial stance matches config value."""
        module = _import_spoon_juror_agent(monkeypatch)
        agent = module.SpoonJurorAgent("test_juror", content_path=CONTENT_PATH, llm=FakeChatBot("ok"))
        assert agent.stance_value == agent.juror_config.initial_stance

    def test_config_property_compatibility(self, monkeypatch):
        """Test config property returns juror_config."""
        module = _import_spoon_juror_agent(monkeypatch)
        agent = module.SpoonJurorAgent("test_juror", content_path=CONTENT_PATH, llm=FakeChatBot("ok"))
        assert agent.config is agent.juror_config
        info = agent.get_info()
        assert set(info.keys()) == {"id", "name", "occupation", "portrait"}


class TestSpoonJurorAgentPrompt:
    """Prompt building tests."""

    def test_build_roleplay_prompt_contains_name(self, monkeypatch):
        """Test roleplay prompt contains juror name."""
        module = _import_spoon_juror_agent(monkeypatch)
        agent = module.SpoonJurorAgent("test_juror", content_path=CONTENT_PATH, llm=FakeChatBot("ok"))
        prompt = agent._build_roleplay_prompt(agent.juror_config)
        assert agent.juror_config.name in prompt
        assert "Topics You Care About" in prompt

    def test_get_stance_description_boundaries(self, monkeypatch):
        """Test stance description at different values."""
        module = _import_spoon_juror_agent(monkeypatch)
        agent = module.SpoonJurorAgent("test_juror", content_path=CONTENT_PATH, llm=FakeChatBot("ok"))
        agent.stance_value = -60
        assert "guilty" in agent._get_stance_description().lower()
        agent.stance_value = 60
        assert "not guilty" in agent._get_stance_description().lower()


class TestSpoonJurorAgentStance:
    """Stance tracking tests."""

    def test_parse_topics_normalizes_mapping(self, monkeypatch):
        """Test topic parsing normalizes aliases."""
        module = _import_spoon_juror_agent(monkeypatch)
        agent = module.SpoonJurorAgent("test_juror", content_path=CONTENT_PATH, llm=FakeChatBot("ok"))
        response = "Reply. <!-- ANALYSIS: {\"topics\": [\"technical_responsibility\"], \"impact\": \"positive\"} -->"
        topics, impact = agent._parse_topics(response)
        assert "technical_responsibility" in topics
        assert impact == "positive"

    def test_update_stance_positive(self, monkeypatch):
        """Test positive impact increases stance."""
        module = _import_spoon_juror_agent(monkeypatch)
        agent = module.SpoonJurorAgent("test_juror", content_path=CONTENT_PATH, llm=FakeChatBot("ok"))
        agent.juror_config.topic_weights = {"technical_responsibility": 20}
        agent.stance_value = 0
        agent._update_stance(["technical_responsibility"], "positive")
        assert agent.stance_value == 20

    def test_update_stance_neutral(self, monkeypatch):
        """Test neutral impact applies reduced weight."""
        module = _import_spoon_juror_agent(monkeypatch)
        agent = module.SpoonJurorAgent("test_juror", content_path=CONTENT_PATH, llm=FakeChatBot("ok"))
        agent.juror_config.topic_weights = {"technical_responsibility": 20}
        agent.stance_value = 0
        agent._update_stance(["technical_responsibility"], "neutral")
        assert agent.stance_value == 6  # 20 * 0.3 = 6

    def test_stance_clamped_upper(self, monkeypatch):
        """Test stance clamped at 100."""
        module = _import_spoon_juror_agent(monkeypatch)
        agent = module.SpoonJurorAgent("test_juror", content_path=CONTENT_PATH, llm=FakeChatBot("ok"))
        agent.juror_config.topic_weights = {"technical_responsibility": 50}
        agent.stance_value = 95
        agent._update_stance(["technical_responsibility"], "positive")
        assert agent.stance_value == 100

    def test_stance_clamped_lower(self, monkeypatch):
        """Test stance clamped at -100."""
        module = _import_spoon_juror_agent(monkeypatch)
        agent = module.SpoonJurorAgent("test_juror", content_path=CONTENT_PATH, llm=FakeChatBot("ok"))
        agent.juror_config.topic_weights = {"technical_responsibility": -50}
        agent.stance_value = -95
        agent._update_stance(["technical_responsibility"], "positive")
        assert agent.stance_value == -100

    def test_get_final_vote(self, monkeypatch):
        """Test final vote based on stance."""
        module = _import_spoon_juror_agent(monkeypatch)
        agent = module.SpoonJurorAgent("test_juror", content_path=CONTENT_PATH, llm=FakeChatBot("ok"))
        agent.stance_value = 50
        assert agent.get_final_vote() is True  # not guilty
        agent.stance_value = -50
        assert agent.get_final_vote() is False  # guilty


class TestSpoonJurorAgentChat:
    """Chat functionality tests."""

    def test_chat_updates_history_and_stance(self, monkeypatch):
        """Test chat updates conversation history and stance."""
        module = _import_spoon_juror_agent(monkeypatch)
        reply = "Hello. <!-- ANALYSIS: {\"topics\": [\"technical_responsibility\"], \"impact\": \"positive\"} -->"
        agent = module.SpoonJurorAgent("test_juror", content_path=CONTENT_PATH, llm=FakeChatBot(reply))
        agent.juror_config.topic_weights = {"technical_responsibility": 20}
        agent.stance_value = 0
        result = asyncio.run(agent.chat("hi"))
        assert "reply" in result
        assert "ANALYSIS" not in result["reply"]
        assert agent.stance_value == 20
        assert len(agent.conversation_history) == 1
        assert len(agent.memory.messages) == 2

    def test_chat_cleans_reply(self, monkeypatch):
        """Test chat removes ANALYSIS tags from reply."""
        module = _import_spoon_juror_agent(monkeypatch)
        reply = "Response text. <!-- ANALYSIS: {\"topics\": [], \"impact\": \"neutral\"} -->"
        agent = module.SpoonJurorAgent("test_juror", content_path=CONTENT_PATH, llm=FakeChatBot(reply))
        result = asyncio.run(agent.chat("test"))
        assert result["reply"] == "Response text."

    @pytest.mark.skip(reason="Requires live LLM API")
    def test_chat_integration(self):
        """Integration test with real LLM."""
        pass


class TestSpoonJurorAgentReset:
    """Reset functionality tests."""

    def test_reset_clears_state(self, monkeypatch):
        """Test reset clears all state."""
        module = _import_spoon_juror_agent(monkeypatch)
        agent = module.SpoonJurorAgent("test_juror", content_path=CONTENT_PATH, llm=FakeChatBot("ok"))
        initial_stance = agent.juror_config.initial_stance
        agent.stance_value = 50
        agent.conversation_history.append(module.ConversationTurn(player="p", juror="j"))
        asyncio.run(agent.add_message("user", "hello"))
        agent.reset()
        assert agent.stance_value == initial_stance
        assert agent.conversation_history == []
        assert agent.memory.messages == []
        assert agent.state == module.AgentState.IDLE
        assert agent.current_step == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
