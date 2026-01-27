"""
SpoonVotingTool tests (unit only, spoon-core mocked).
"""
import asyncio
import importlib
import sys
import types
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).parent.parent))


def _install_spoon_ai_stubs(monkeypatch):
    """Install spoon-core stubs for isolated testing."""
    spoon_ai = types.ModuleType("spoon_ai")
    agents = types.ModuleType("spoon_ai.agents")
    toolcall = types.ModuleType("spoon_ai.agents.toolcall")
    chat = types.ModuleType("spoon_ai.chat")
    tools = types.ModuleType("spoon_ai.tools")
    schema = types.ModuleType("spoon_ai.schema")
    tools_base = types.ModuleType("spoon_ai.tools.base")

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


def _import_spoon_voting_tool(monkeypatch):
    """Import SpoonVotingTool with mocked spoon-core."""
    _install_spoon_ai_stubs(monkeypatch)
    if "tools.spoon_voting_tool" in sys.modules:
        del sys.modules["tools.spoon_voting_tool"]
    return importlib.import_module("tools.spoon_voting_tool")


class DummyCall:
    """Dummy callable for mocking contract functions."""
    def __init__(self, value=None, raises=None):
        self._value = value
        self._raises = raises
        self.called = False

    def call(self):
        self.called = True
        if self._raises is not None:
            raise self._raises
        return self._value


class DummyFunctions:
    """Dummy contract functions for testing."""
    def __init__(self, state_tuple=None, verdict=None, raises=None):
        self._state_tuple = state_tuple
        self._verdict = verdict
        self._raises = raises
        self.get_vote_state_call = DummyCall(value=state_tuple, raises=raises)
        self.get_verdict_call = DummyCall(value=verdict, raises=raises)

    def getVoteState(self):
        return self.get_vote_state_call

    def getVerdict(self):
        return self.get_verdict_call


class DummyContract:
    """Dummy contract for testing."""
    def __init__(self, functions):
        self.functions = functions


class TestCastVoteToolSchema:
    """CastVoteTool schema tests."""

    def test_cast_vote_tool_schema(self, monkeypatch):
        """Test CastVoteTool has correct schema."""
        module = _import_spoon_voting_tool(monkeypatch)
        tool = module.CastVoteTool(
            contract_address="0x0000000000000000000000000000000000000000",
            rpc_url="http://127.0.0.1:8545",
            private_keys=[],
        )
        assert tool.name == "cast_vote"
        assert "juror_index" in tool.parameters["properties"]
        assert "guilty" in tool.parameters["properties"]
        assert "juror_index" in tool.parameters["required"]
        assert "guilty" in tool.parameters["required"]

    def test_cast_vote_tool_to_param(self, monkeypatch):
        """Test CastVoteTool converts to OpenAI format."""
        module = _import_spoon_voting_tool(monkeypatch)
        tool = module.CastVoteTool(
            contract_address="0x0000000000000000000000000000000000000000",
            private_keys=[],
        )
        param = tool.to_param()
        assert param["type"] == "function"
        assert param["function"]["name"] == "cast_vote"
        assert "parameters" in param["function"]


class TestGetVoteStateToolSchema:
    """GetVoteStateTool schema tests."""

    def test_get_vote_state_tool_schema(self, monkeypatch):
        """Test GetVoteStateTool has correct schema."""
        module = _import_spoon_voting_tool(monkeypatch)
        tool = module.GetVoteStateTool(
            contract_address="0x0000000000000000000000000000000000000000",
            rpc_url="http://127.0.0.1:8545",
        )
        assert tool.name == "get_vote_state"
        assert tool.parameters["properties"] == {}
        assert tool.parameters["required"] == []


class TestCastVoteToolValidation:
    """CastVoteTool parameter validation tests."""

    def test_cast_vote_invalid_index_raises(self, monkeypatch):
        """Test invalid juror index raises ToolFailure."""
        module = _import_spoon_voting_tool(monkeypatch)
        tool = module.CastVoteTool(
            contract_address="0x0000000000000000000000000000000000000000",
            rpc_url="http://127.0.0.1:8545",
            private_keys=["key1"],
        )
        monkeypatch.setattr(module.CastVoteTool, "_ensure_initialized", lambda self: None)
        with pytest.raises(module.ToolFailure):
            asyncio.run(tool.execute(juror_index=2, guilty=True))

    def test_cast_vote_negative_index_raises(self, monkeypatch):
        """Test negative juror index raises ToolFailure."""
        module = _import_spoon_voting_tool(monkeypatch)
        tool = module.CastVoteTool(
            contract_address="0x0000000000000000000000000000000000000000",
            rpc_url="http://127.0.0.1:8545",
            private_keys=["key1"],
        )
        monkeypatch.setattr(module.CastVoteTool, "_ensure_initialized", lambda self: None)
        with pytest.raises(module.ToolFailure):
            asyncio.run(tool.execute(juror_index=-1, guilty=False))


class TestGetVoteStateToolExecution:
    """GetVoteStateTool execution tests."""

    def test_get_vote_state_failure_raises_toolfailure(self, monkeypatch):
        """Test contract failure raises ToolFailure."""
        module = _import_spoon_voting_tool(monkeypatch)
        tool = module.GetVoteStateTool(
            contract_address="0x0000000000000000000000000000000000000000",
            rpc_url="http://127.0.0.1:8545",
        )
        functions = DummyFunctions(raises=RuntimeError("boom"))
        tool._contract = DummyContract(functions)
        monkeypatch.setattr(module.GetVoteStateTool, "_ensure_initialized", lambda self: None)
        with pytest.raises(module.ToolFailure):
            asyncio.run(tool.execute())

    def test_get_vote_state_open_no_verdict(self, monkeypatch):
        """Test open voting returns no verdict."""
        module = _import_spoon_voting_tool(monkeypatch)
        tool = module.GetVoteStateTool(
            contract_address="0x0000000000000000000000000000000000000000",
            rpc_url="http://127.0.0.1:8545",
        )
        functions = DummyFunctions(state_tuple=(1, 2, 3, False), verdict="N/A")
        tool._contract = DummyContract(functions)
        monkeypatch.setattr(module.GetVoteStateTool, "_ensure_initialized", lambda self: None)
        result = asyncio.run(tool.execute())
        assert result["guilty_votes"] == 1
        assert result["not_guilty_votes"] == 2
        assert result["total_voted"] == 3
        assert result["voting_closed"] is False
        assert result["verdict"] is None
        assert functions.get_verdict_call.called is False

    def test_get_vote_state_closed_with_verdict(self, monkeypatch):
        """Test closed voting returns verdict."""
        module = _import_spoon_voting_tool(monkeypatch)
        tool = module.GetVoteStateTool(
            contract_address="0x0000000000000000000000000000000000000000",
            rpc_url="http://127.0.0.1:8545",
        )
        functions = DummyFunctions(state_tuple=(1, 2, 3, True), verdict="GUILTY")
        tool._contract = DummyContract(functions)
        monkeypatch.setattr(module.GetVoteStateTool, "_ensure_initialized", lambda self: None)
        result = asyncio.run(tool.execute())
        assert result["verdict"] == "GUILTY"
        assert functions.get_verdict_call.called is True


class TestCloseVotingToolSchema:
    """CloseVotingTool schema tests."""

    def test_close_voting_tool_schema(self, monkeypatch):
        """Test CloseVotingTool has correct schema."""
        module = _import_spoon_voting_tool(monkeypatch)
        tool = module.CloseVotingTool(
            contract_address="0x0000000000000000000000000000000000000000",
            private_keys=[],
        )
        assert tool.name == "close_voting"
        assert tool.parameters["properties"] == {}


class TestIntegration:
    """Integration tests (skipped by default)."""

    @pytest.mark.skip(reason="Requires blockchain node/web3 setup")
    def test_cast_vote_integration(self):
        """Integration test with real blockchain."""
        pass

    @pytest.mark.skip(reason="Requires blockchain node/web3 setup")
    def test_get_vote_state_integration(self):
        """Integration test with real blockchain."""
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
