"""
Deliberation unit tests (backend-only).
"""
import asyncio
import importlib
import sys
import types
from dataclasses import dataclass
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).parent.parent))


def _install_spoon_ai_stubs(monkeypatch):
    """Install minimal spoon_ai stubs for isolated testing."""
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
        async def ask(self, messages, system_msg):
            return "OK"

        async def ask_tool(self, messages, system_msg, tools=None, tool_choice=None):
            return "OK"

    class ToolManager:
        last_instance = None

        def __init__(self, tools_list):
            self.tools = tools_list
            ToolManager.last_instance = self

        def to_params(self):
            params = []
            for tool in self.tools:
                if hasattr(tool, "to_param"):
                    params.append(tool.to_param())
                else:
                    params.append({"type": "function", "function": {"name": getattr(tool, "name", "")}})
            return params

        def get_tool(self, name):
            for tool in self.tools:
                if getattr(tool, "name", "") == name:
                    return tool
            return None

    class AgentState:
        IDLE = "IDLE"

    class ToolChoice:
        AUTO = "auto"
        NONE = "none"

    class ToolCall:
        def __init__(self, id, function):
            self.id = id
            self.function = function

    class Function:
        def __init__(self, name, arguments):
            self.name = name
            self.arguments = arguments

        @staticmethod
        def create(name, arguments):
            return Function(name, arguments)

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

        async def add_message(self, role, content, **kwargs):
            message = {"role": role, "content": content}
            message.update(kwargs)
            self.memory.messages.append(message)

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
    schema.ToolCall = ToolCall
    schema.Function = Function
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


def _import_orchestrator(monkeypatch):
    _install_spoon_ai_stubs(monkeypatch)
    if "services.deliberation_orchestrator" in sys.modules:
        del sys.modules["services.deliberation_orchestrator"]
    return importlib.import_module("services.deliberation_orchestrator")


@dataclass
class DummyConfig:
    topic_weights: dict[str, int]
    speaker_power: float = 0.5


@dataclass
class DummyAgent:
    juror_id: str
    stance_value: int
    juror_config: DummyConfig


def _make_session():
    session_module = importlib.import_module("services.session_manager")
    return session_module.SessionState(session_id="s1", phase=session_module.Phase.deliberation)


def test_select_leader_distance_priority(monkeypatch):
    orchestrator_module = _import_orchestrator(monkeypatch)
    agents = {
        "a": DummyAgent("a", 10, DummyConfig({})),
        "b": DummyAgent("b", 50, DummyConfig({})),
        "c": DummyAgent("c", 60, DummyConfig({})),
    }
    orchestrator = orchestrator_module.DeliberationOrchestrator(agents)
    session = _make_session()
    leader = orchestrator.select_leader(session)
    assert leader == "a"


def test_select_leader_tiebreak(monkeypatch):
    orchestrator_module = _import_orchestrator(monkeypatch)
    agents = {
        "a": DummyAgent("a", 10, DummyConfig({})),
        "b": DummyAgent("b", 90, DummyConfig({})),
    }
    orchestrator = orchestrator_module.DeliberationOrchestrator(agents)
    session = _make_session()
    session.leader_history.append("a")
    leader = orchestrator.select_leader(session)
    assert leader == "b"


def test_select_responders_max_conflict(monkeypatch):
    orchestrator_module = _import_orchestrator(monkeypatch)
    agents = {
        "leader": DummyAgent("leader", 50, DummyConfig({})),
        "a": DummyAgent("a", 10, DummyConfig({})),
        "b": DummyAgent("b", 90, DummyConfig({})),
        "c": DummyAgent("c", 60, DummyConfig({})),
    }
    orchestrator = orchestrator_module.DeliberationOrchestrator(agents)
    session = _make_session()
    responders = orchestrator.select_responders("leader", session)
    assert set(responders) == {"a", "b"}


def test_stance_update_formula(monkeypatch):
    orchestrator_module = _import_orchestrator(monkeypatch)
    speaker = DummyAgent("s", 60, DummyConfig({}, speaker_power=0.5))
    listener = DummyAgent("l", 60, DummyConfig({"technical_responsibility": 10}))
    orchestrator = orchestrator_module.DeliberationOrchestrator({"s": speaker, "l": listener})
    deltas = orchestrator.apply_stance_impact(
        speaker=speaker,
        listeners=[listener],
        topics=["technical_responsibility"],
        impact="positive",
    )
    assert deltas["l"] == 5
    assert listener.stance_value == 65


def test_stance_clamp_bounds(monkeypatch):
    orchestrator_module = _import_orchestrator(monkeypatch)
    speaker = DummyAgent("s", 60, DummyConfig({}, speaker_power=1.0))
    listener = DummyAgent("l", 99, DummyConfig({"technical_responsibility": 20}))
    orchestrator = orchestrator_module.DeliberationOrchestrator({"s": speaker, "l": listener})
    deltas = orchestrator.apply_stance_impact(
        speaker=speaker,
        listeners=[listener],
        topics=["technical_responsibility"],
        impact="positive",
    )
    assert deltas["l"] == 6
    assert listener.stance_value == 100


def test_extreme_stance_damping(monkeypatch):
    orchestrator_module = _import_orchestrator(monkeypatch)
    speaker = DummyAgent("s", 90, DummyConfig({}, speaker_power=1.0))
    listener = DummyAgent("l", 90, DummyConfig({"technical_responsibility": 10}))
    orchestrator = orchestrator_module.DeliberationOrchestrator({"s": speaker, "l": listener})
    deltas = orchestrator.apply_stance_impact(
        speaker=speaker,
        listeners=[listener],
        topics=["technical_responsibility"],
        impact="positive",
    )
    assert deltas["l"] == 5
    assert listener.stance_value == 95


def test_distance_100_zero_impact(monkeypatch):
    orchestrator_module = _import_orchestrator(monkeypatch)
    speaker = DummyAgent("s", 0, DummyConfig({}, speaker_power=1.0))
    listener = DummyAgent("l", 100, DummyConfig({"technical_responsibility": 10}))
    orchestrator = orchestrator_module.DeliberationOrchestrator({"s": speaker, "l": listener})
    deltas = orchestrator.apply_stance_impact(
        speaker=speaker,
        listeners=[listener],
        topics=["technical_responsibility"],
        impact="positive",
    )
    assert deltas["l"] == 0
    assert listener.stance_value == 100


def test_note_limit_enforcement(monkeypatch):
    orchestrator_module = _import_orchestrator(monkeypatch)
    session = _make_session()
    session.notes_used = 3
    agents = {"j1": DummyAgent("j1", 50, DummyConfig({}))}
    orchestrator = orchestrator_module.DeliberationOrchestrator(agents)
    with pytest.raises(PermissionError):
        orchestrator.submit_note(session, "j1", "note", "k1")


def test_note_idempotency(monkeypatch):
    orchestrator_module = _import_orchestrator(monkeypatch)
    session = _make_session()
    agents = {"j1": DummyAgent("j1", 50, DummyConfig({}))}
    orchestrator = orchestrator_module.DeliberationOrchestrator(agents)
    first = orchestrator.submit_note(session, "j1", "note", "k1")
    assert first["accepted"] is True
    assert session.notes_used == 1
    second = orchestrator.submit_note(session, "j1", "note", "k1")
    assert second["accepted"] is False
    assert session.notes_used == 1


def test_cast_vote_blocked_in_deliberation(monkeypatch):
    _install_spoon_ai_stubs(monkeypatch)
    if "agents.spoon_juror_agent" in sys.modules:
        del sys.modules["agents.spoon_juror_agent"]
    agent_module = importlib.import_module("agents.spoon_juror_agent")

    class FakeChatBot:
        def __init__(self):
            self.last_tools = None

        async def ask_tool(self, messages, system_msg, tools=None, tool_choice=None):
            self.last_tools = tools
            return "OK <!-- ANALYSIS: {\"topics\": [], \"impact\": \"neutral\"} -->"

    content_path = str(Path(__file__).parent.parent.parent / "content" / "jurors")
    llm = FakeChatBot()
    agent = agent_module.SpoonJurorAgent(
        "j1",
        content_path=content_path,
        llm=llm,
        voting_config={"contract_address": "0x0", "rpc_url": "http://127.0.0.1:8545", "private_keys": []},
    )
    agent.max_steps = 1

    asyncio.run(agent.debate("context", role="leader"))
    assert llm.last_tools is not None
    tool_names = [tool.get("function", {}).get("name") for tool in llm.last_tools]
    assert "cast_vote" not in tool_names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
