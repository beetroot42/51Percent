"""
EvidenceLookupTool tests.
"""
import asyncio
import json
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


def _install_spoon_ai_stubs(monkeypatch):
    """Install spoon-core stubs for isolated testing."""
    spoon_ai = types.ModuleType("spoon_ai")
    tools = types.ModuleType("spoon_ai.tools")
    tools_base = types.ModuleType("spoon_ai.tools.base")

    class BaseTool:
        name = ""
        description = ""
        parameters = {}

        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
            
            # Mock Pydantic Field handling
            for key in dir(self):
                if key.startswith("_") or key in kwargs:
                    continue
                val = getattr(self.__class__, key, None)
                if val and hasattr(val, "default"):
                    setattr(self, key, val.default)

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
    spoon_ai.tools = tools

    monkeypatch.setitem(sys.modules, "spoon_ai", spoon_ai)
    monkeypatch.setitem(sys.modules, "spoon_ai.tools", tools)
    monkeypatch.setitem(sys.modules, "spoon_ai.tools.base", tools_base)


CONTENT_PATH = str(Path(__file__).parent.parent.parent / "content")


class TestEvidenceLookupTool:
    """Evidence lookup tool tests."""

    def test_valid_evidence_ids(self, monkeypatch):
        """Test tool accepts valid evidence IDs."""
        _install_spoon_ai_stubs(monkeypatch)
        if "tools.evidence_tool" in sys.modules:
            del sys.modules["tools.evidence_tool"]
        from tools.evidence_tool import EvidenceLookupTool

        tool = EvidenceLookupTool(content_path=CONTENT_PATH)
        assert tool.name == "lookup_evidence"
        assert "chat_history" in tool.parameters["properties"]["evidence_id"]["enum"]
        assert "log_injection" in tool.parameters["properties"]["evidence_id"]["enum"]
        assert "safety_report" in tool.parameters["properties"]["evidence_id"]["enum"]
        assert "dossier" in tool.parameters["properties"]["evidence_id"]["enum"]

    def test_invalid_evidence_id_raises(self, monkeypatch):
        """Test invalid evidence ID raises ToolFailure."""
        _install_spoon_ai_stubs(monkeypatch)
        if "tools.evidence_tool" in sys.modules:
            del sys.modules["tools.evidence_tool"]
        from tools.evidence_tool import EvidenceLookupTool
        from spoon_ai.tools.base import ToolFailure

        tool = EvidenceLookupTool(content_path=CONTENT_PATH)
        with pytest.raises(ToolFailure) as exc_info:
            asyncio.run(tool.execute("invalid_id"))
        assert "Unknown evidence_id" in str(exc_info.value)

    def test_execute_chat_history(self, monkeypatch):
        """Test loading chat_history evidence."""
        _install_spoon_ai_stubs(monkeypatch)
        if "tools.evidence_tool" in sys.modules:
            del sys.modules["tools.evidence_tool"]
        from tools.evidence_tool import EvidenceLookupTool

        tool = EvidenceLookupTool(content_path=CONTENT_PATH)
        evidence_file = Path(CONTENT_PATH) / "case" / "evidence" / "chat_history.json"
        if evidence_file.exists():
            result = asyncio.run(tool.execute("chat_history"))
            assert isinstance(result, str)
            assert len(result) > 0

    def test_execute_dossier(self, monkeypatch):
        """Test loading dossier evidence with special formatting."""
        _install_spoon_ai_stubs(monkeypatch)
        if "tools.evidence_tool" in sys.modules:
            del sys.modules["tools.evidence_tool"]
        from tools.evidence_tool import EvidenceLookupTool

        tool = EvidenceLookupTool(content_path=CONTENT_PATH)
        dossier_file = Path(CONTENT_PATH) / "case" / "dossier.json"
        if dossier_file.exists():
            result = asyncio.run(tool.execute("dossier"))
            assert isinstance(result, str)
            # Dossier has special formatting with sections
            assert len(result) > 0

    def test_missing_file_raises(self, monkeypatch, tmp_path):
        """Test missing evidence file raises ToolFailure."""
        _install_spoon_ai_stubs(monkeypatch)
        if "tools.evidence_tool" in sys.modules:
            del sys.modules["tools.evidence_tool"]
        from tools.evidence_tool import EvidenceLookupTool
        from spoon_ai.tools.base import ToolFailure

        tool = EvidenceLookupTool(content_path=str(tmp_path))
        with pytest.raises(ToolFailure) as exc_info:
            asyncio.run(tool.execute("chat_history"))
        assert "not found" in str(exc_info.value)

    def test_invalid_json_raises(self, monkeypatch, tmp_path):
        """Test invalid JSON file raises ToolFailure."""
        _install_spoon_ai_stubs(monkeypatch)
        if "tools.evidence_tool" in sys.modules:
            del sys.modules["tools.evidence_tool"]
        from tools.evidence_tool import EvidenceLookupTool
        from spoon_ai.tools.base import ToolFailure

        # Create invalid JSON file
        evidence_dir = tmp_path / "case" / "evidence"
        evidence_dir.mkdir(parents=True)
        (evidence_dir / "chat_history.json").write_text("invalid json {")

        tool = EvidenceLookupTool(content_path=str(tmp_path))
        with pytest.raises(ToolFailure) as exc_info:
            asyncio.run(tool.execute("chat_history"))
        assert "Invalid evidence JSON" in str(exc_info.value)

    def test_to_param_format(self, monkeypatch):
        """Test tool parameter format for LLM integration."""
        _install_spoon_ai_stubs(monkeypatch)
        if "tools.evidence_tool" in sys.modules:
            del sys.modules["tools.evidence_tool"]
        from tools.evidence_tool import EvidenceLookupTool

        tool = EvidenceLookupTool(content_path=CONTENT_PATH)
        param = tool.to_param()
        assert param["type"] == "function"
        assert param["function"]["name"] == "lookup_evidence"
        assert "evidence_id" in param["function"]["parameters"]["properties"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
