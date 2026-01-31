"""
Deliberation orchestrator for juror debate phase.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable

from agents.spoon_juror_agent import SpoonJurorAgent, TOPIC_MAPPING
from services.session_manager import SessionState


@dataclass
class DeliberationSpeaker:
    juror_id: str
    role: str  # "leader" | "responder"


class DeliberationOrchestrator:
    def __init__(self, agents: dict[str, SpoonJurorAgent]) -> None:
        self.agents = agents

    def select_leader(self, session: SessionState) -> str:
        candidates = list(self.agents.values())
        if not candidates:
            raise ValueError("No jurors available")

        leader_counts: dict[str, int] = {}
        for juror_id in session.leader_history:
            leader_counts[juror_id] = leader_counts.get(juror_id, 0) + 1

        # Prefer jurors who have not led yet (for 4 rounds / 5 jurors)
        never_led = [agent for agent in candidates if leader_counts.get(agent.juror_id, 0) == 0]
        pool = never_led or candidates

        def sort_key(agent: SpoonJurorAgent) -> tuple[int, int, str]:
            distance = abs(agent.stance_value - 50)
            return (-distance, leader_counts.get(agent.juror_id, 0), agent.juror_id)

        pool.sort(key=sort_key)
        return pool[0].juror_id

    def select_responders(self, leader_id: str, session: SessionState) -> list[str]:
        responders = [agent for agent in self.agents.values() if agent.juror_id != leader_id]
        if len(responders) <= 2:
            return [agent.juror_id for agent in responders]

        responder_counts: dict[str, int] = {}
        for round_list in session.responder_history:
            for juror_id in round_list:
                responder_counts[juror_id] = responder_counts.get(juror_id, 0) + 1

        leader = self.agents[leader_id]

        def sort_key(agent: SpoonJurorAgent) -> tuple[int, int, str]:
            distance = abs(agent.stance_value - leader.stance_value)
            return (-distance, responder_counts.get(agent.juror_id, 0), agent.juror_id)

        responders.sort(key=sort_key)
        return [agent.juror_id for agent in responders[:2]]

    async def run_round(
        self,
        round_num: int,
        session: SessionState,
        notes_for_round: dict[str, str] | None = None,
    ) -> list[dict]:
        leader_id = self.select_leader(session)
        responder_ids = self.select_responders(leader_id, session)

        session.leader_history.append(leader_id)
        session.responder_history.append(list(responder_ids))

        speakers = [DeliberationSpeaker(leader_id, "leader")]
        speakers.extend([DeliberationSpeaker(juror_id, "responder") for juror_id in responder_ids])

        round_events: list[dict] = []

        for speaker in speakers:
            context = self.build_debate_context(session, round_num)
            agent = self.agents[speaker.juror_id]
            note = None
            if notes_for_round and speaker.juror_id in notes_for_round:
                note = notes_for_round.get(speaker.juror_id)

            stances_before = {juror_id: member.stance_value for juror_id, member in self.agents.items()}
            before = agent.stance_value
            response = await agent.debate(context=context, role=speaker.role, note=note)
            reply_text = response.get("reply", "")
            tool_actions = response.get("tool_actions", [])
            topics = response.get("topics", [])
            impact = response.get("impact", "neutral")

            deltas = self.apply_stance_impact(
                speaker=agent,
                listeners=[a for a in self.agents.values() if a.juror_id != speaker.juror_id],
                topics=topics,
                impact=impact,
            )
            stances_after = {juror_id: member.stance_value for juror_id, member in self.agents.items()}

            session.deliberation_transcript.append({
                "round": round_num,
                "speaker_id": speaker.juror_id,
                "role": speaker.role,
                "text": reply_text,
                "tool_actions": tool_actions,
                "speaker_stance_before": before,
                "speaker_stance_after": agent.stance_value,
                "stances_before": stances_before,
                "stances_after": stances_after,
                "stance_deltas": deltas,
            })

            round_events.append({
                "speaker_id": speaker.juror_id,
                "role": speaker.role,
                "text": reply_text,
                "stance_deltas": deltas,
            })

        return round_events

    def apply_stance_impact(
        self,
        speaker: SpoonJurorAgent,
        listeners: Iterable[SpoonJurorAgent],
        topics: list[str],
        impact: str,
    ) -> dict[str, int]:
        impact_factor = 0.3
        if impact == "positive":
            impact_factor = 1.0
        elif impact == "negative":
            impact_factor = -1.0

        speaker_power = getattr(speaker.juror_config, "speaker_power", 0.5) if speaker.juror_config else 0.5

        deltas: dict[str, int] = {}
        for listener in listeners:
            delta_total = 0.0
            for topic in topics:
                normalized = TOPIC_MAPPING.get(topic, topic)
                weight = 0
                if listener.juror_config and normalized in listener.juror_config.topic_weights:
                    weight = listener.juror_config.topic_weights.get(normalized, 0)
                if weight == 0 and listener.juror_config:
                    for orig, norm in TOPIC_MAPPING.items():
                        if norm == normalized and orig in listener.juror_config.topic_weights:
                            weight = listener.juror_config.topic_weights.get(orig, 0)
                            break

                distance_damping = 1 - abs(listener.stance_value - speaker.stance_value) / 100
                if distance_damping < 0:
                    distance_damping = 0.0
                delta_total += weight * impact_factor * speaker_power * distance_damping

            if listener.stance_value < 15 or listener.stance_value > 85:
                delta_total *= 0.5

            delta = int(round(delta_total))
            if delta != 0:
                listener.stance_value = max(0, min(100, listener.stance_value + delta))
            deltas[listener.juror_id] = delta

        return deltas

    def build_debate_context(self, session: SessionState, round_num: int) -> str:
        transcript = session.deliberation_transcript
        if not transcript:
            return "暂无辩论记录。"

        rounds: dict[int, list[dict]] = {}
        for entry in transcript:
            rounds.setdefault(entry.get("round", 0), []).append(entry)

        sorted_rounds = sorted(rounds.keys())
        recent_rounds = sorted_rounds[-2:]
        older_rounds = [r for r in sorted_rounds if r not in recent_rounds]

        context_parts: list[str] = []
        if older_rounds:
            summary_lines: list[str] = []
            for r in older_rounds:
                for entry in rounds.get(r, []):
                    summary_lines.append(f"R{r} {entry.get('speaker_id')}({entry.get('role')}): {entry.get('text')}")
            summary = "\n".join(summary_lines)
            if len(summary) > 300:
                summary = summary[:300] + "..."
            context_parts.append("【早期摘要】\n" + summary)

        for r in recent_rounds:
            context_parts.append(f"【第{r}轮记录】")
            for entry in rounds.get(r, []):
                context_parts.append(
                    f"{entry.get('speaker_id')}({entry.get('role')}): {entry.get('text')}"
                )

        return "\n".join(context_parts)

    def submit_note(self, session: SessionState, target_id: str, content: str, key: str) -> dict[str, Any]:
        if not key:
            raise ValueError("idempotency key required")
        if target_id not in self.agents:
            raise ValueError("juror not found")
        if len(content) > 200:
            raise ValueError("note too long")
        if key in session.note_keys:
            return {"accepted": False, "notes_remaining": max(0, 3 - session.notes_used)}
        if session.notes_used >= 3:
            raise PermissionError("note limit reached")

        session.note_keys.add(key)
        session.notes_used += 1
        session.deliberation_notes[target_id] = content
        return {"accepted": True, "notes_remaining": max(0, 3 - session.notes_used)}
