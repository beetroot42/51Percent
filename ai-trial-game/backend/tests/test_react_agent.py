"""
ReAct Agent tests - tool loop and AgentManager integration.
"""
import asyncio
import importlib
import json
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
            self._tool_calls = kwargs.get("tool_calls", [])

        async def ask(self, messages, system_msg):
            if self.reply_text is not None:
                return self.reply_text
            return "Default reply. <!-- ANALYSIS: {\"topics\": [], \"impact\": \"neutral\"} -->"

        async def ask_with_tools(self, messages, system_msg, tools):
            content = self.reply_text or "Response text. <!-- ANALYSIS: {\"topics\": [], \"impact\": \"neutral\"} -->"
            return (content, self._tool_calls)

    class ToolManager:
        def __init__(self, tools_list):
            self.tools = tools_list

        def get_tool(self, name):
            for tool in self.tools:
                if getattr(tool, "name", "") == name:
                    return tool
            return None

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

            # Handle kwargs (passed by super().__init__ in real code)
            for k, v in kwargs.items():
                setattr(self, k, v)

            # Mock Pydantic Field handling - extract defaults from class fields if not set
            for key in dir(self):
                if key in ["max_steps", "tool_choices"]:
                    if hasattr(self, key) and not isinstance(getattr(self, key), (int, str, list, dict, bool, type(None))):
                        # If it's a FieldInfo object (or similar descriptor), replace with default
                        val = getattr(self.__class__, key, None)
                        if val and hasattr(val, "default"):
                            setattr(self, key, val.default)
                    elif not hasattr(self, key):
                         val = getattr(self.__class__, key, None)
                         if val and hasattr(val, "default"):
                            setattr(self, key, val.default)

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


def _import_modules(monkeypatch):
    """Import modules with mocked spoon-core."""
    _install_spoon_ai_stubs(monkeypatch)
    for mod in ["agents.spoon_juror_agent", "tools.evidence_tool", "services.agent_manager"]:
        if mod in sys.modules:
            del sys.modules[mod]
    agent_module = importlib.import_module("agents.spoon_juror_agent")
    return agent_module


class FakeChatBotWithTools:
    """Fake ChatBot that can return tool calls."""

    def __init__(self, reply_text=None, tool_calls=None):
        self.reply_text = reply_text or "Response. <!-- ANALYSIS: {\"topics\": [], \"impact\": \"neutral\"} -->"
        self._tool_calls = tool_calls or []
        self._call_count = 0

    async def ask(self, messages, system_msg):
        return self.reply_text

    async def ask_with_tools(self, messages, system_msg, tools):
        self._call_count += 1
        # First call returns tool calls, second call returns final response
        if self._call_count == 1 and self._tool_calls:
            return ("", self._tool_calls)
        return (self.reply_text, [])


class TestReActToolLoop:
    """Tests for ReAct tool calling loop."""

    def test_tool_choices_auto_by_default(self, monkeypatch):
        """Test tool_choices defaults to AUTO."""
        module = _import_modules(monkeypatch)
        agent = module.SpoonJurorAgent(
            "test_juror",
            content_path=CONTENT_PATH,
            llm=FakeChatBotWithTools()
        )
        assert agent.tool_choices == module.ToolChoice.AUTO

    def test_max_steps_default(self, monkeypatch):
        """Test max_steps defaults to 3."""
        module = _import_modules(monkeypatch)
        agent = module.SpoonJurorAgent(
            "test_juror",
            content_path=CONTENT_PATH,
            llm=FakeChatBotWithTools()
        )
        assert agent.max_steps == 3

    def test_evidence_tool_injected(self, monkeypatch):
        """Test EvidenceLookupTool is injected."""
        module = _import_modules(monkeypatch)
        agent = module.SpoonJurorAgent(
            "test_juror",
            content_path=CONTENT_PATH,
            llm=FakeChatBotWithTools()
        )
        tool_names = [t.name for t in agent.available_tools.tools]
        assert "lookup_evidence" in tool_names

    def test_voting_tool_injected_with_config(self, monkeypatch):
        """Test CastVoteTool is injected when voting_config provided."""
        module = _import_modules(monkeypatch)
        voting_config = {
            "contract_address": "0x123",
            "private_key": "0xabc",
            "rpc_url": "http://localhost:8545",
            "juror_index": 0,
        }
        agent = module.SpoonJurorAgent(
            "test_juror",
            content_path=CONTENT_PATH,
            llm=FakeChatBotWithTools(),
            voting_config=voting_config
        )
        tool_names = [t.name for t in agent.available_tools.tools]
        assert "cast_vote" in tool_names

    def test_chat_returns_tool_actions(self, monkeypatch):
        """Test chat returns tool_actions in response."""
        module = _import_modules(monkeypatch)
        agent = module.SpoonJurorAgent(
            "test_juror",
            content_path=CONTENT_PATH,
            llm=FakeChatBotWithTools()
        )
        result = asyncio.run(agent.chat("test message"))
        assert "tool_actions" in result
        assert isinstance(result["tool_actions"], list)

    def test_chat_returns_has_voted(self, monkeypatch):
        """Test chat returns has_voted in response."""
        module = _import_modules(monkeypatch)
        agent = module.SpoonJurorAgent(
            "test_juror",
            content_path=CONTENT_PATH,
            llm=FakeChatBotWithTools()
        )
        result = asyncio.run(agent.chat("test message"))
        assert "has_voted" in result
        assert isinstance(result["has_voted"], bool)

    def test_extract_tool_calls_tuple(self, monkeypatch):
        """Test _extract_tool_calls handles tuple response."""
        module = _import_modules(monkeypatch)
        agent = module.SpoonJurorAgent(
            "test_juror",
            content_path=CONTENT_PATH,
            llm=FakeChatBotWithTools()
        )
        content, calls = agent._extract_tool_calls(("hello", [{"name": "test"}]))
        assert content == "hello"
        assert len(calls) == 1

    def test_extract_tool_calls_dict(self, monkeypatch):
        """Test _extract_tool_calls handles dict response."""
        module = _import_modules(monkeypatch)
        agent = module.SpoonJurorAgent(
            "test_juror",
            content_path=CONTENT_PATH,
            llm=FakeChatBotWithTools()
        )
        content, calls = agent._extract_tool_calls({
            "content": "response",
            "tool_calls": [{"name": "lookup_evidence"}]
        })
        assert content == "response"
        assert len(calls) == 1

    def test_extract_tool_calls_string(self, monkeypatch):
        """Test _extract_tool_calls handles string response."""
        module = _import_modules(monkeypatch)
        agent = module.SpoonJurorAgent(
            "test_juror",
            content_path=CONTENT_PATH,
            llm=FakeChatBotWithTools()
        )
        content, calls = agent._extract_tool_calls("plain string")
        assert content == "plain string"
        assert calls == []

    def test_parse_tool_call_dict(self, monkeypatch):
        """Test _parse_tool_call extracts name and args from dict."""
        module = _import_modules(monkeypatch)
        agent = module.SpoonJurorAgent(
            "test_juror",
            content_path=CONTENT_PATH,
            llm=FakeChatBotWithTools()
        )
        name, args, narrative = agent._parse_tool_call({
            "name": "lookup_evidence",
            "arguments": {"evidence_id": "chat_history"}
        })
        assert name == "lookup_evidence"
        assert args["evidence_id"] == "chat_history"

    def test_parse_tool_call_json_string_args(self, monkeypatch):
        """Test _parse_tool_call handles JSON string arguments."""
        module = _import_modules(monkeypatch)
        agent = module.SpoonJurorAgent(
            "test_juror",
            content_path=CONTENT_PATH,
            llm=FakeChatBotWithTools()
        )
        name, args, narrative = agent._parse_tool_call({
            "name": "lookup_evidence",
            "arguments": '{"evidence_id": "dossier"}'
        })
        assert name == "lookup_evidence"
        assert args["evidence_id"] == "dossier"

    def test_parse_tool_call_extracts_narrative(self, monkeypatch):
        """Test _parse_tool_call extracts narrative field."""
        module = _import_modules(monkeypatch)
        agent = module.SpoonJurorAgent(
            "test_juror",
            content_path=CONTENT_PATH,
            llm=FakeChatBotWithTools()
        )
        name, args, narrative = agent._parse_tool_call({
            "name": "lookup_evidence",
            "arguments": {"evidence_id": "chat_history", "narrative": "Let me check..."}
        })
        assert narrative == "Let me check..."

    def test_summarize_tool_result_short(self, monkeypatch):
        """Test _summarize_tool_result returns full text for short results."""
        module = _import_modules(monkeypatch)
        agent = module.SpoonJurorAgent(
            "test_juror",
            content_path=CONTENT_PATH,
            llm=FakeChatBotWithTools()
        )
        summary = agent._summarize_tool_result("Short result")
        assert summary == "Short result"

    def test_summarize_tool_result_truncates(self, monkeypatch):
        """Test _summarize_tool_result truncates long results."""
        module = _import_modules(monkeypatch)
        agent = module.SpoonJurorAgent(
            "test_juror",
            content_path=CONTENT_PATH,
            llm=FakeChatBotWithTools()
        )
        long_text = "x" * 300
        summary = agent._summarize_tool_result(long_text, limit=100)
        assert len(summary) <= 103  # 100 + "..."
        assert summary.endswith("...")

    def test_system_prompt_includes_tool_instructions(self, monkeypatch):
        """Test system prompt includes tool usage instructions."""
        module = _import_modules(monkeypatch)
        agent = module.SpoonJurorAgent(
            "test_juror",
            content_path=CONTENT_PATH,
            llm=FakeChatBotWithTools()
        )
        assert "lookup_evidence" in agent.system_prompt
        assert "cast_vote" in agent.system_prompt
        assert "Tool Usage Rules" in agent.system_prompt


class TestAgentManagerVotingConfig:
    """Tests for AgentManager voting config injection."""

    def test_voting_config_stored(self, monkeypatch):
        """Test voting_config is stored in AgentManager."""
        _install_spoon_ai_stubs(monkeypatch)
        if "services.agent_manager" in sys.modules:
            del sys.modules["services.agent_manager"]
        from services.agent_manager import AgentManager

        voting_config = {"contract_address": "0x123", "private_key": "0xabc"}
        manager = AgentManager(voting_config=voting_config)
        assert manager.voting_config == voting_config

    def test_juror_index_injected(self, monkeypatch):
        """Test juror_index is injected to each agent."""
        module = _import_modules(monkeypatch)
        if "services.agent_manager" in sys.modules:
            del sys.modules["services.agent_manager"]
        from services.agent_manager import AgentManager

        voting_config = {
            "contract_address": "0x123",
            "private_key": "0xabc",
            "rpc_url": "http://localhost:8545"
        }
        manager = AgentManager(juror_ids=["test_juror"], voting_config=voting_config)
        manager.load_all_jurors(content_path=CONTENT_PATH)

        # Check that juror has _juror_index set
        agent = manager.get_juror("test_juror")
        assert agent._juror_index == 0

    def test_no_voting_config_no_index(self, monkeypatch):
        """Test no juror_index when voting_config is None."""
        module = _import_modules(monkeypatch)
        if "services.agent_manager" in sys.modules:
            del sys.modules["services.agent_manager"]
        from services.agent_manager import AgentManager

        manager = AgentManager(juror_ids=["test_juror"])
        manager.load_all_jurors(content_path=CONTENT_PATH)

        agent = manager.get_juror("test_juror")
        assert agent._juror_index is None


class TestChatResponse:
    """Tests for chat response structure."""

    def test_chat_response_structure(self, monkeypatch):
        """Test chat returns all expected fields."""
        module = _import_modules(monkeypatch)
        agent = module.SpoonJurorAgent(
            "test_juror",
            content_path=CONTENT_PATH,
            llm=FakeChatBotWithTools()
        )
        result = asyncio.run(agent.chat("test"))

        assert "reply" in result
        assert "juror_id" in result
        assert "stance_label" in result
        assert "tool_actions" in result
        assert "has_voted" in result

    def test_tool_action_structure(self, monkeypatch):
        """Test tool_actions items have expected structure."""
        module = _import_modules(monkeypatch)

        # Create a fake tool that returns a result
        class FakeTool:
            name = "lookup_evidence"
            def execute(self, **kwargs):
                return "Evidence content here"

        tool_calls = [{
            "name": "lookup_evidence",
            "arguments": {"evidence_id": "chat_history"}
        }]

        llm = FakeChatBotWithTools(tool_calls=tool_calls)
        agent = module.SpoonJurorAgent(
            "test_juror",
            content_path=CONTENT_PATH,
            llm=llm
        )

        # Replace tool with fake
        for i, t in enumerate(agent.available_tools.tools):
            if t.name == "lookup_evidence":
                agent.available_tools.tools[i] = FakeTool()
                break

        result = asyncio.run(agent.chat("show me the chat history"))

        if result["tool_actions"]:
            action = result["tool_actions"][0]
            assert "tool" in action
            assert "input" in action
            assert "result_summary" in action
            assert "narrative" in action


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
