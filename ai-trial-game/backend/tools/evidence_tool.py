"""
EvidenceLookupTool - evidence lookup tool.

Allows agents to read case evidence details from JSON files.
"""

import json
from pathlib import Path
from typing import Any

from pydantic import Field

from spoon_ai.tools.base import BaseTool, ToolFailure


class EvidenceLookupTool(BaseTool):
    """Tool for reading case evidence details."""

    name: str = "lookup_evidence"
    description: str = (
        "Read case evidence details. Available evidence_ids: "
        "chat_history, log_injection, safety_report, dossier."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "evidence_id": {
                "type": "string",
                "enum": ["chat_history", "log_injection", "safety_report", "dossier"],
                "description": "Evidence ID to load",
            }
        },
        "required": ["evidence_id"],
    }

    content_path: str = Field(default="content")

    _evidence_paths: dict[str, str] = {
        "chat_history": "case/evidence/chat_history.json",
        "log_injection": "case/evidence/log_injection.json",
        "safety_report": "case/evidence/safety_report.json",
        "dossier": "case/dossier.json",
    }

    model_config = {"arbitrary_types_allowed": True}

    def _resolve_base_path(self) -> Path:
        base_path = Path(self.content_path)
        if base_path.is_absolute():
            return base_path
        backend_dir = Path(__file__).resolve().parent.parent
        return (backend_dir.parent / base_path).resolve()

    async def execute(self, evidence_id: str) -> str:
        """Load evidence content by ID."""
        if evidence_id not in self._evidence_paths:
            raise ToolFailure(
                f"Unknown evidence_id: {evidence_id}. "
                f"Available: {', '.join(self._evidence_paths.keys())}"
            )

        base_path = self._resolve_base_path()
        evidence_file = base_path / self._evidence_paths[evidence_id]

        if not evidence_file.exists():
            raise ToolFailure(f"Evidence file not found: {evidence_file}")

        try:
            data: dict[str, Any] = json.loads(evidence_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ToolFailure(f"Invalid evidence JSON: {exc}") from exc

        if evidence_id == "dossier":
            title = data.get("title", "Case Dossier")
            summary = data.get("summary", "")
            sections = data.get("sections", [])
            content_parts = [title, summary]
            for section in sections:
                section_title = section.get("title", "")
                section_content = section.get("content", "")
                if section_title:
                    content_parts.append(f"\n## {section_title}")
                if section_content:
                    content_parts.append(section_content)
            return "\n".join(part for part in content_parts if part).strip()

        name = data.get("name", evidence_id)
        short_desc = data.get("short_description", "")
        content = data.get("content", "")
        parts = [name, short_desc, "", content]
        return "\n".join(part for part in parts if part).strip()
