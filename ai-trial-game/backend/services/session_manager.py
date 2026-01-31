"""
Session state management for the game flow.
"""

from __future__ import annotations

import json
import uuid
from enum import Enum
from pathlib import Path
import re

from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[2]
JUROR_CONTENT = PROJECT_ROOT / "content" / "jurors"
EVIDENCE_CONTENT = PROJECT_ROOT / "content" / "case" / "evidence"


class Phase(str, Enum):
    prologue = "prologue"
    investigation = "investigation"
    persuasion = "persuasion"
    verdict = "verdict"


class SessionState(BaseModel):
    session_id: str
    phase: Phase
    evidence_unlocked: set[str] = Field(default_factory=set)
    witness_nodes: dict[str, str] = Field(default_factory=dict)
    witness_rounds_used: dict[str, int] = Field(default_factory=dict)
    blake_round: int = 0
    juror_rounds_used: dict[str, int] = Field(default_factory=dict)
    juror_stance: dict[str, int] = Field(default_factory=dict)


class SessionManager:
    def __init__(self, juror_content: Path | None = None) -> None:
        self._sessions: dict[str, SessionState] = {}
        self._juror_content = juror_content or JUROR_CONTENT

    def _load_initial_juror_stances(self) -> dict[str, int]:
        if not self._juror_content.exists():
            return {}

        stances: dict[str, int] = {}
        selected_paths: dict[str, Path] = {}
        for path in sorted(self._juror_content.glob("*.json")):
            if path.name == "_template.json":
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
            juror_id = data.get("id", path.stem)
            if juror_id in selected_paths:
                existing = selected_paths[juror_id]
                if path.stem.isascii() and not existing.stem.isascii():
                    selected_paths[juror_id] = path
                    stances[juror_id] = int(data.get("initial_stance", 0))
                continue
            selected_paths[juror_id] = path
            stances[juror_id] = int(data.get("initial_stance", 0))
        return stances

    def create_session(self) -> SessionState:
        session_id = uuid.uuid4().hex
        state = SessionState(
            session_id=session_id,
            phase=Phase.prologue,
            evidence_unlocked=self._load_initial_evidence_unlocked(),
            juror_stance=self._load_initial_juror_stances(),
        )
        self._sessions[session_id] = state
        return state

    def get(self, session_id: str) -> SessionState:
        if session_id not in self._sessions:
            raise KeyError(f"Session not found: {session_id}")
        return self._sessions[session_id]

    def unlock_evidence(self, session_id: str, evidence_ids: list[str]) -> None:
        state = self.get(session_id)
        for evidence_id in evidence_ids:
            state.evidence_unlocked.add(evidence_id)

    def get_witness_node(self, session_id: str, witness_id: str) -> str:
        state = self.get(session_id)
        return state.witness_nodes.get(witness_id, "start")

    def set_witness_node(self, session_id: str, witness_id: str, node_id: str) -> None:
        state = self.get(session_id)
        state.witness_nodes[witness_id] = node_id

    def increment_witness_rounds(self, session_id: str, witness_id: str) -> int:
        state = self.get(session_id)
        current = state.witness_rounds_used.get(witness_id, 0) + 1
        state.witness_rounds_used[witness_id] = current
        return current

    def _load_initial_evidence_unlocked(self) -> set[str]:
        if not EVIDENCE_CONTENT.exists():
            return set()

        unlocked: set[str] = set()
        for path in sorted(EVIDENCE_CONTENT.glob("*.json")):
            if path.name == "_template.json":
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            internal_id = str(data.get("id", "")).upper()
            if re.match(r"^E([1-9]|10)$", internal_id):
                unlocked.add(path.stem)
        return unlocked


def require_phase(state: SessionState, *phases: Phase) -> None:
    if phases and state.phase not in phases:
        allowed = ", ".join([phase.value for phase in phases])
        raise ValueError(f"Invalid phase. Expected: {allowed}.")
