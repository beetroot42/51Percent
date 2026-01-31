"""
Agent Manager

Responsibilities:
- Manage all SpoonJurorAgent instances
- Provide a unified chat interface
- Collect votes and compute verdicts
"""

import json
import re
from pathlib import Path

from agents.spoon_juror_agent import SpoonJurorAgent


class AgentManager:
    """Manage multiple juror agents for a single game session."""

    def __init__(self, juror_ids: list[str] | None = None, voting_config: dict | None = None):
        """
        Initialize agent manager.

        Args:
            juror_ids: Optional list of juror IDs to load.
            voting_config: Optional voting tool config for juror tool calls.
        """
        self.agents: dict[str, SpoonJurorAgent] = {}
        self.juror_ids = juror_ids or []
        self.voting_config = voting_config

    def load_all_jurors(self, content_path: str | None = None) -> None:
        """
        Load all juror agents.

        Args:
            content_path: Juror character card directory path.
        """
        content_dir = self._resolve_content_path(content_path)

        if not self.juror_ids:
            juror_files: dict[str, Path] = {}
            for path in sorted(content_dir.glob("*.json")):
                if path.name == "_template.json" or path.name.startswith("test_"):
                    continue
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    continue
                juror_id = str(data.get("id", path.stem))
                existing = juror_files.get(juror_id)
                if existing is None:
                    juror_files[juror_id] = path
                else:
                    if path.stem.isascii() and not existing.stem.isascii():
                        juror_files[juror_id] = path

            def _sort_key(value: str) -> tuple[int, int | str]:
                match = re.match(r"^j(\d+)$", value.lower())
                if match:
                    return (0, int(match.group(1)))
                return (1, value)

            self.juror_ids = sorted(juror_files.keys(), key=_sort_key)

        for index, juror_id in enumerate(self.juror_ids):
            if juror_id not in self.agents:
                agent_voting_config = None
                if self.voting_config:
                    agent_voting_config = dict(self.voting_config)
                    agent_voting_config["juror_index"] = index
                self.agents[juror_id] = SpoonJurorAgent(
                    juror_id=juror_id,
                    content_path=str(content_dir),
                    voting_config=agent_voting_config
                )

    def get_juror(self, juror_id: str) -> SpoonJurorAgent:
        """
        Get a specific juror agent.

        Args:
            juror_id: Juror ID.

        Returns:
            JurorAgent instance.

        Raises:
            KeyError: If juror not found.
        """
        if juror_id not in self.agents:
            raise KeyError(f"Juror not found: {juror_id}")
        return self.agents[juror_id]

    async def chat_with_juror(self, juror_id: str, message: str) -> dict:
        """
        Chat with a juror.

        Args:
            juror_id: Juror ID.
            message: Player message.

        Returns:
            {"reply": str, "juror_id": str, "stance_label": str}
        """
        agent = self.get_juror(juror_id)
        return await agent.chat(message)

    def get_all_juror_info(self) -> list[dict]:
        """
        Get basic info for all jurors (for frontend display).

        Returns:
            [{"id": str, "name": str, "first_message": str}, ...]
        """
        info_list = []
        for juror_id, agent in self.agents.items():
            info_list.append({
                "id": juror_id,
                "name": agent.config.name if agent.config else "",
                "first_message": agent.get_first_message(),
                "codename": agent.config.codename if agent.config else "",
                "stance_label": agent._get_stance_label(),
            })
        return info_list

    def collect_votes(self) -> dict:
        """
        Collect votes from all jurors.

        Returns:
            {
                "votes": {
                    "juror_id": {"name": str, "vote": "GUILTY"|"NOT_GUILTY"},
                    ...
                },
                "guilty_count": int,
                "not_guilty_count": int,
                "verdict": "GUILTY"|"NOT_GUILTY"
            }
        """
        votes: dict[str, dict] = {}
        guilty_count = 0
        not_guilty_count = 0

        for juror_id, agent in self.agents.items():
            guilty = agent.get_final_vote()
            vote_label = "GUILTY" if guilty else "NOT_GUILTY"
            votes[juror_id] = {
                "name": agent.config.name if agent.config else juror_id,
                "vote": vote_label
            }
            if guilty:
                guilty_count += 1
            else:
                not_guilty_count += 1

        verdict = "NOT_GUILTY" if not_guilty_count >= guilty_count else "GUILTY"

        return {
            "votes": votes,
            "guilty_count": guilty_count,
            "not_guilty_count": not_guilty_count,
            "verdict": verdict
        }

    def reset_all(self) -> None:
        """Reset all agents for a new game."""
        for agent in self.agents.values():
            agent.reset()

    def _resolve_content_path(self, content_path: str | None) -> Path:
        """
        Resolve content path for juror cards, with a safe fallback.
        """
        if content_path:
            content_dir = Path(content_path)
            if content_dir.exists():
                return content_dir

        project_root = Path(__file__).resolve().parents[2]
        fallback_dir = project_root / "content" / "jurors"
        return fallback_dir
