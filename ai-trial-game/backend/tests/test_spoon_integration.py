"""
SpoonOS integration tests.

Validates SpoonJurorAgent compatibility.
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSpoonAgentImport:
    """SpoonOS import tests."""

    def test_spoon_core_import(self):
        """Verify SpoonOS imports."""
        try:
            from spoon_ai.agents.toolcall import ToolCallAgent
            from spoon_ai.chat import ChatBot, Memory
            from spoon_ai.tools.base import BaseTool
            assert True
        except ImportError as e:
            pytest.skip(f"spoon-core not installed: {e}")

    def test_spoon_juror_agent_import(self):
        """Verify SpoonJurorAgent import."""
        try:
            from agents.spoon_juror_agent import SpoonJurorAgent
            assert SpoonJurorAgent is not None
        except ImportError as e:
            pytest.skip(f"SpoonJurorAgent import failed: {e}")

    def test_spoon_voting_tool_import(self):
        """Verify SpoonVotingTool import."""
        try:
            from tools.spoon_voting_tool import CastVoteTool, GetVoteStateTool
            assert CastVoteTool is not None
            assert GetVoteStateTool is not None
        except ImportError as e:
            pytest.skip(f"SpoonVotingTool import failed: {e}")


class TestAgentManager:
    """AgentManager tests."""

    def test_agent_manager_init(self):
        """Test AgentManager init."""
        from services.agent_manager import AgentManager

        manager = AgentManager()
        assert manager.agents == {}
        assert manager.juror_ids == []


class TestSpoonJurorAgentCompatibility:
    """SpoonJurorAgent interface tests."""

    @pytest.fixture
    def content_path(self):
        """Get juror config directory."""
        return str(Path(__file__).parent.parent.parent / "content" / "jurors")

    def test_config_loading(self, content_path):
        """Test config loading."""
        try:
            from agents.spoon_juror_agent import SpoonJurorAgent
        except ImportError:
            pytest.skip("SpoonJurorAgent not available")

        # Check if juror config files exist
        config_dir = Path(content_path)
        if not config_dir.exists():
            pytest.skip(f"Content path not found: {content_path}")

        json_files = list(config_dir.glob("*.json"))
        json_files = [f for f in json_files if not f.name.startswith("_") and not f.name.startswith("test_")]

        if not json_files:
            pytest.skip("No juror config files found")

        juror_id = json_files[0].stem

        # Only test config loading; no LLM required
        config = SpoonJurorAgent._load_juror_config(juror_id, content_path)
        assert config.id == juror_id
        assert config.name is not None

    def test_interface_methods(self, content_path):
        """Test SpoonJurorAgent interface methods."""
        try:
            from agents.spoon_juror_agent import SpoonJurorAgent
        except ImportError:
            pytest.skip("SpoonJurorAgent not available")

        # Verify required methods exist
        required_methods = {'chat', 'get_final_vote', 'get_first_message', 'get_info', 'reset'}
        agent_methods = set(dir(SpoonJurorAgent))

        for method in required_methods:
            assert method in agent_methods, f"Missing method: {method}"


class TestSpoonVotingToolSchema:
    """SpoonVotingTool JSON schema tests."""

    def test_cast_vote_tool_schema(self):
        """Test CastVoteTool parameter schema."""
        try:
            from tools.spoon_voting_tool import CastVoteTool
        except ImportError:
            pytest.skip("CastVoteTool not available")

        tool = CastVoteTool(
            contract_address="0x0000000000000000000000000000000000000000",
            private_keys=[]
        )

        assert tool.name == "cast_vote"
        assert "juror_index" in tool.parameters["properties"]
        assert "guilty" in tool.parameters["properties"]

    def test_get_vote_state_tool_schema(self):
        """Test GetVoteStateTool parameter schema."""
        try:
            from tools.spoon_voting_tool import GetVoteStateTool
        except ImportError:
            pytest.skip("GetVoteStateTool not available")

        tool = GetVoteStateTool(
            contract_address="0x0000000000000000000000000000000000000000"
        )

        assert tool.name == "get_vote_state"
        assert tool.parameters["properties"] == {}

    def test_tool_to_param_format(self):
        """Test tool conversion to OpenAI format."""
        try:
            from tools.spoon_voting_tool import CastVoteTool
        except ImportError:
            pytest.skip("CastVoteTool not available")

        tool = CastVoteTool(
            contract_address="0x0000000000000000000000000000000000000000",
            private_keys=[]
        )

        param = tool.to_param()
        assert param["type"] == "function"
        assert param["function"]["name"] == "cast_vote"
        assert "parameters" in param["function"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
