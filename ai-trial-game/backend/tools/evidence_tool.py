"""
EvidenceLookupTool - evidence lookup tool.

Allows agents to read case evidence details from JSON files.
"""

import json
import re
from pathlib import Path
from typing import Any

from pydantic import Field

from spoon_ai.tools.base import BaseTool, ToolFailure


class EvidenceLookupTool(BaseTool):
    """Tool for reading case evidence details."""

    name: str = "lookup_evidence"
    description: str = (
        "Read case evidence details by id, file stem, or internal id (e.g., E1)."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "evidence_id": {
                "type": "string",
                "description": "Evidence ID, file stem, or internal id (e.g., E1)",
            },
            "evidence_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Multiple evidence IDs to load in one call",
            },
        },
        "required": [],
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

    def _normalize_internal_id(self, value: str) -> str:
        match = re.match(r"^E0*(\d+)$", value.strip(), flags=re.IGNORECASE)
        if match:
            return f"E{int(match.group(1))}"
        return value.strip().upper()

    def _resolve_evidence_file(self, evidence_id: str) -> Path:
        base_path = self._resolve_base_path()
        if evidence_id in self._evidence_paths:
            return base_path / self._evidence_paths[evidence_id]

        evidence_dir = base_path / "case" / "evidence"
        direct_path = evidence_dir / f"{evidence_id}.json"
        if direct_path.exists():
            return direct_path

        normalized = self._normalize_internal_id(evidence_id)
        for path in sorted(evidence_dir.glob("*.json")):
            if path.name == "_template.json":
                continue
            try:
                data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            internal_id = self._normalize_internal_id(str(data.get("id", "")))
            if internal_id and internal_id == normalized:
                return path

        return direct_path

    def _format_dossier(self, data: dict[str, Any]) -> str:
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

    def _format_evidence(self, evidence_id: str, evidence_file: Path, data: dict[str, Any]) -> str:
        if evidence_id == "dossier" or evidence_file.name == "dossier.json":
            return self._format_dossier(data)

        name = data.get("name", evidence_id)
        short_desc = data.get("short_description", "")
        content = data.get("content", "")
        parts = [name, short_desc, "", content]
        return "\n".join(part for part in parts if part).strip()

    def _format_label(self, evidence_id: str, evidence_file: Path, data: dict[str, Any]) -> str:
        internal_id = str(data.get("id", "")).strip()
        name = data.get("name", evidence_file.stem)
        label_parts = []
        if internal_id:
            label_parts.append(internal_id)
        label_parts.append(name)
        label_parts.append(f"file:{evidence_file.stem}")
        return " | ".join(label_parts)

    async def execute(self, evidence_id: str | None = None, evidence_ids: list[str] | None = None) -> str:
        """Load evidence content by ID."""
        requested: list[str] = []
        if evidence_ids:
            requested.extend([str(item) for item in evidence_ids if str(item).strip()])
        if evidence_id:
            requested.append(str(evidence_id))

        if not requested:
            raise ToolFailure("evidence_id or evidence_ids is required")

        base_path = self._resolve_base_path()
        results: list[str] = []

        for raw_id in requested:
            evidence_file = self._resolve_evidence_file(raw_id)
            if not evidence_file.exists():
                raise ToolFailure(f"Evidence file not found: {evidence_file}")

            try:
                data: dict[str, Any] = json.loads(evidence_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise ToolFailure(f"Invalid evidence JSON: {exc}") from exc

            content = self._format_evidence(raw_id, evidence_file, data)
            if len(requested) == 1:
                return content
            label = self._format_label(raw_id, evidence_file, data)
            results.append(f"## {label}\n{content}")

        return "\n\n".join(results).strip()
