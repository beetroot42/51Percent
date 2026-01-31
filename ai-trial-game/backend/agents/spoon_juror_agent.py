"""
SpoonJurorAgent - SpoonOS juror agent implementation.

Extends ToolCallAgent and keeps the JurorAgent business logic
(stance tracking, topic parsing, etc.).
"""

import json
import re
from uuid import uuid4
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Any

from pydantic import Field

# spoon-core imports
from spoon_ai.agents.toolcall import ToolCallAgent
from spoon_ai.chat import ChatBot, Memory
from spoon_ai.tools import ToolManager
from spoon_ai.schema import AgentState, ToolChoice, ToolCall, Function

from tools.evidence_tool import EvidenceLookupTool
from tools.spoon_voting_tool import CastVoteTool

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEAKNESS_IMPACT = 10


def load_file(path: str) -> str:
    """Load a UTF-8 text file relative to project root."""
    file_path = Path(path)
    if not file_path.is_absolute():
        file_path = PROJECT_ROOT / file_path
    try:
        return file_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


@dataclass
class JurorConfig:
    """Juror configuration loaded from JSON."""
    id: str
    name: str
    codename: str
    role_prompt: str
    weakness: dict
    background: str
    personality: list[str]
    speaking_style: str
    initial_stance: int
    topic_weights: dict[str, int]
    first_message: str
    age: int = 0
    occupation: str = ""
    portrait: str = ""


@dataclass
class ConversationTurn:
    """Single conversation turn."""
    player: str
    juror: str


# Topic name mapping (Chinese and English)
TOPIC_MAPPING = {
    "技术责任": "technical_responsibility",
    "外部攻击": "external_attack",
    "AI自主性": "ai_autonomy",
    "情感诉求": "emotional_appeal",
    "法律先例": "legal_precedent",
    "受害者立场": "victim_position",
    "安全措施": "safety_measures",
    "企业责任": "corporate_responsibility",
    "社会影响": "social_impact",
    "技术细节": "technical_details",
    "technical_responsibility": "technical_responsibility",
    "external_attack": "external_attack",
    "ai_autonomy": "ai_autonomy",
    "emotional_appeal": "emotional_appeal",
    "legal_precedent": "legal_precedent",
    "victim_position": "victim_position",
    "safety_measures": "safety_measures",
    "corporate_responsibility": "corporate_responsibility",
    "social_impact": "social_impact",
    "technical_details": "technical_details",
}


class SpoonJurorAgent(ToolCallAgent):
    """
    SpoonOS juror agent.

    Extends ToolCallAgent for lifecycle management while keeping
    stance tracking and topic parsing logic.
    """

    # Override ToolCallAgent defaults
    tool_choices: Any = Field(default=ToolChoice.AUTO)  # Allow tool calls
    max_steps: int = Field(default=3)  # Allow tool loop

    # Business state
    juror_id: str = Field(default="")
    juror_config: Optional[JurorConfig] = Field(default=None, exclude=True)
    stance_value: int = Field(default=0)
    conversation_history: List[ConversationTurn] = Field(default_factory=list, exclude=True)
    last_vote: Optional[bool] = Field(default=None, exclude=True)

    # Internal state
    _content_path: str = ""
    _evidence_index_cache: str = ""

    model_config = {"arbitrary_types_allowed": True}

    def __init__(
        self,
        juror_id: str,
        content_path: str = "content/jurors",
        llm: Optional[ChatBot] = None,
        voting_config: Optional[dict] = None,
        **kwargs
    ):
        """
        Initialize SpoonJurorAgent.

        Args:
            juror_id: Juror ID, matches JSON filename
            content_path: Character card directory
            llm: ChatBot instance (optional, defaults from env)
        """
        # Load config
        config = self._load_juror_config(juror_id, content_path)

        # Build ChatBot if not provided
        if llm is None:
            llm = ChatBot(
                llm_provider=os.getenv("LLM_PROVIDER", "openai"),
                model_name=os.getenv("OPENAI_COMPATIBLE_MODEL", "claude-sonnet-4-5-20250929"),
                api_key=os.getenv("OPENAI_COMPATIBLE_API_KEY") or os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_COMPATIBLE_BASE_URL") or os.getenv("OPENAI_BASE_URL"),
            )

        # Build system prompt (pass initial_stance before self is initialized)
        evidence_index = SpoonJurorAgent._build_evidence_index_from_content(content_path)
        system_prompt = self._build_roleplay_prompt(
            config,
            stance_value=config.initial_stance,
            evidence_index=evidence_index
        )

        # Build tool list
        content_base_path = Path(content_path)
        if content_base_path.name == "jurors":
            content_base_path = content_base_path.parent
        tools_list = [EvidenceLookupTool(content_path=str(content_base_path))]
        self._juror_index: Optional[int] = None
        if voting_config:
            voting_config = dict(voting_config)
            if "juror_index" in voting_config:
                self._juror_index = voting_config.pop("juror_index")
            tools_list.append(CastVoteTool(**voting_config))
        available_tools = ToolManager(tools_list)

        # Initialize base agent
        super().__init__(
            name=f"juror_{juror_id}",
            description=f"Juror {config.name}",
            system_prompt=system_prompt,
            llm=llm,
            memory=Memory(),
            available_tools=available_tools,
            **kwargs
        )

        # Set business state
        self.juror_id = juror_id
        self.juror_config = config
        self.stance_value = max(0, min(100, config.initial_stance))
        self.conversation_history = []  # Explicitly initialize
        self._content_path = content_path

    @staticmethod
    def _load_juror_config(juror_id: str, content_path: str) -> JurorConfig:
        """Load juror config from JSON."""
        config_file = Path(content_path) / f"{juror_id}.json"

        if not config_file.exists():
            content_dir = Path(content_path)
            matches: list[Path] = []
            for path in sorted(content_dir.glob("*.json")):
                if path.name == "_template.json":
                    continue
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    continue
                if data.get("id") == juror_id:
                    matches.append(path)
            if matches:
                ascii_matches = [path for path in matches if path.stem.isascii()]
                config_file = ascii_matches[0] if ascii_matches else matches[0]

        if not config_file.exists():
            raise FileNotFoundError(f"Juror config not found: {config_file}")

        with open(config_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        return JurorConfig(
            id=data["id"],
            name=data["name"],
            codename=data.get("codename", ""),
            role_prompt=data.get("role_prompt", ""),
            weakness=data.get("weakness", {}),
            background=data.get("background", ""),
            personality=data.get("personality", []),
            speaking_style=data.get("speaking_style", ""),
            initial_stance=data.get("initial_stance", 0),
            topic_weights=data.get("topic_weights", {}),
            first_message=data.get("first_message", ""),
            age=data.get("age", 0),
            occupation=data.get("occupation", ""),
            portrait=data.get("portrait", ""),
        )

    def _build_roleplay_prompt(
        self,
        config: JurorConfig,
        stance_value: int = None,
        evidence_index: str | None = None
    ) -> str:
        """Build the roleplay system prompt."""
        common_prefix = load_file("content/prompts/common_prefix.md")
        role_prompt = config.role_prompt or ""
        common_suffix = load_file("content/prompts/juror_suffix.md")
        current_stance = stance_value if stance_value is not None else self.stance_value
        if evidence_index is None:
            evidence_index = self._get_evidence_index()

        return f"""{common_prefix}

## 你的角色
{role_prompt}

## 当前状态
- 你的有罪倾向值: {current_stance}/100
- 不要在对话中提及这个数值

## 可查证物索引
{evidence_index}
- 你可以主动查阅证物，不需要玩家出示
- lookup_evidence 支持一次查询多个证物（evidence_ids 列表）

{common_suffix}
"""

    @staticmethod
    def _build_evidence_index_from_content(content_path: str) -> str:
        base_path = Path(content_path) if content_path else PROJECT_ROOT / "content"
        if base_path.name == "jurors":
            base_path = base_path.parent
        evidence_dir = base_path / "case" / "evidence"
        lines: list[str] = []
        if evidence_dir.exists():
            for path in sorted(evidence_dir.glob("*.json")):
                if path.name == "_template.json":
                    continue
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    continue
                internal_id = str(data.get("id", path.stem)).strip()
                name = data.get("name", path.stem)
                lines.append(f"- {internal_id}: {name} (file:{path.stem})")
        return "\n".join(lines) if lines else "- (无证物索引)"

    def _get_evidence_index(self) -> str:
        if self._evidence_index_cache:
            return self._evidence_index_cache

        self._evidence_index_cache = self._build_evidence_index_from_content(self._content_path)
        return self._evidence_index_cache

    def _get_stance_description_for_value(self, stance_value: int) -> str:
        """Generate stance description for a value."""
        if stance_value > 80:
            return "你强烈倾向于判定有罪"
        elif stance_value > 60:
            return "你倾向于判定有罪，但仍愿意听取不同意见"
        elif stance_value > 40:
            return "你目前没有明确立场，正在权衡双方论点"
        elif stance_value > 20:
            return "你倾向于判定无罪，但仍有一些疑虑"
        else:
            return "你强烈倾向于判定无罪"

    def _get_stance_description(self) -> str:
        """Convenience wrapper for current stance."""
        return self._get_stance_description_for_value(self.stance_value)

    async def chat(self, player_message: str) -> dict:
        """
        One round of dialogue with the player (legacy-compatible interface).

        Args:
            player_message: Player input

        Returns:
            {
                "reply": str,
                "juror_id": str,
                "stance_label": str,
                "tool_actions": list[dict],
                "has_voted": bool
            }
        """
        # Weakness detection
        weakness_triggered = False
        if self.juror_config and self.juror_config.weakness:
            keywords = self.juror_config.weakness.get("trigger_keywords", [])
            if any(kw in player_message for kw in keywords):
                weakness_triggered = True
                if self.stance_value > 50:
                    self.stance_value -= WEAKNESS_IMPACT
                elif self.stance_value < 50:
                    self.stance_value += WEAKNESS_IMPACT
                self.stance_value = max(0, min(100, self.stance_value))

        # Add user message to memory
        await self.add_message("user", player_message)

        # Refresh system prompt (stance may have changed)
        self.system_prompt = self._build_roleplay_prompt(self.juror_config)

        tool_actions: list[dict] = []
        has_voted = False
        final_reply: str | None = None
        accumulated_text_parts: list[str] = []

        for _ in range(self.max_steps):
            response = await self._ask_with_tools()
            reply_text, tool_calls = self._extract_tool_calls(response)

            if reply_text:
                accumulated_text_parts.append(reply_text)

            if tool_calls:
                normalized_tool_calls = self._normalize_tool_calls(tool_calls)
                await self.add_message(
                    "assistant",
                    reply_text or "",
                    tool_calls=normalized_tool_calls
                )

                for call, norm_call in zip(tool_calls, normalized_tool_calls):
                    tool_name, tool_args, narrative, tool_call_id = self._parse_tool_call(call)
                    if not tool_call_id:
                        tool_call_id = norm_call.id
                    if not tool_name:
                        tool_name = norm_call.function.name
                    exec_args = dict(tool_args)
                    exec_args.pop("narrative", None)
                    if tool_name == "cast_vote" and "juror_index" not in exec_args:
                        if self._juror_index is not None:
                            exec_args["juror_index"] = self._juror_index

                    tool_result = await self._execute_tool(tool_name, exec_args)
                    result_summary = self._summarize_tool_result(tool_result)
                    tool_actions.append({
                        "tool": tool_name,
                        "input": exec_args,
                        "result_summary": result_summary,
                        "narrative": narrative,
                    })
                    if tool_name == "cast_vote":
                        has_voted = True
                        self.last_vote = bool(exec_args.get("guilty"))

                    await self.add_message(
                        "tool",
                        tool_result,
                        tool_call_id=tool_call_id,
                        tool_name=tool_name
                    )
                continue

            final_reply = reply_text or str(response)
            await self.add_message("assistant", final_reply)
            break

        if final_reply is None:
            if accumulated_text_parts:
                final_reply = "\n".join(accumulated_text_parts)
            else:
                final_reply = "让我再仔细想想这个案件。"

        # Parse topic tags
        topics, impact = self._parse_topics(final_reply)

        # Update stance
        self._update_stance(topics, impact)

        # Clean reply (remove tags)
        clean_reply = self._clean_reply(final_reply)
        if not clean_reply:
            clean_reply = "（陪审员正在思考...）"

        # Record conversation history
        self.conversation_history.append(ConversationTurn(
            player=player_message,
            juror=clean_reply
        ))

        return {
            "reply": clean_reply,
            "juror_id": self.juror_id,
            "stance_label": self._get_stance_label(),
            "tool_actions": tool_actions,
            "has_voted": has_voted,
            "weakness_triggered": weakness_triggered
        }

    def _parse_topics(self, response: str) -> tuple[list[str], str]:
        """Parse topic tags from agent reply."""
        match = re.search(r'<!-- ANALYSIS: ({.*?}) -->', response, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
                topics = data.get("topics", [])
                impact = data.get("impact", "neutral")
                normalized_topics = [TOPIC_MAPPING.get(t, t) for t in topics]
                return normalized_topics, impact
            except json.JSONDecodeError:
                pass
        return [], "neutral"

    def _update_stance(self, topics: list[str], impact: str) -> None:
        """Update hidden stance based on topics."""
        for topic in topics:
            weight = 0
            if topic in self.juror_config.topic_weights:
                weight = self.juror_config.topic_weights[topic]
            else:
                for orig, norm in TOPIC_MAPPING.items():
                    if norm == topic and orig in self.juror_config.topic_weights:
                        weight = self.juror_config.topic_weights[orig]
                        break

            if weight != 0:
                if impact == "negative":
                    weight = -weight * 0.5
                elif impact == "neutral":
                    weight = weight * 0.3
                self.stance_value += int(weight)

        self.stance_value = max(0, min(100, self.stance_value))

    def _clean_reply(self, response: str) -> str:
        """Clean reply by removing hidden tags."""
        cleaned = re.sub(r'<!-- ANALYSIS:.*?-->', '', response, flags=re.DOTALL)
        return cleaned.strip()

    async def _ask_with_tools(self) -> Any:
        """Call LLM with tool support when available."""
        if hasattr(self.llm, "ask_tool"):
            tools_payload = None
            if hasattr(self.available_tools, "to_params"):
                tools_payload = self.available_tools.to_params()
            else:
                tools_payload = self.available_tools
            return await self.llm.ask_tool(
                messages=self.memory.messages,
                system_msg=self.system_prompt,
                tools=tools_payload,
                tool_choice=getattr(self, "tool_choices", None),
            )
        return await self.llm.ask(messages=self.memory.messages, system_msg=self.system_prompt)

    def _extract_tool_calls(self, response: Any) -> tuple[str, list[dict]]:
        """Normalize LLM response into (content, tool_calls)."""
        if isinstance(response, tuple) and len(response) == 2:
            content, tool_calls = response
            return str(content) if content is not None else "", list(tool_calls or [])
        if isinstance(response, dict):
            content = response.get("content") or response.get("reply") or ""
            tool_calls = response.get("tool_calls") or []
            return str(content) if content is not None else "", list(tool_calls or [])
        content = getattr(response, "content", None)
        tool_calls = getattr(response, "tool_calls", None)
        if content is not None or tool_calls is not None:
            return str(content) if content is not None else "", list(tool_calls or [])
        if isinstance(response, str):
            return response, []
        return str(response), []

    def _parse_tool_call(self, call: Any) -> tuple[str, dict, str, str | None]:
        """Extract tool name, args, narrative, and tool_call_id from a tool call."""
        tool_call_id = None
        if isinstance(call, dict):
            func = call.get("function") or {}
            tool_name = call.get("name") or func.get("name") or ""
            raw_args = call.get("arguments") or func.get("arguments") or call.get("input") or {}
            tool_call_id = call.get("id")
        else:
            tool_name = getattr(call, "name", "") or getattr(getattr(call, "function", None), "name", "")
            raw_args = getattr(call, "arguments", None) or getattr(getattr(call, "function", None), "arguments", None) or {}
            tool_call_id = getattr(call, "id", None)

        if isinstance(raw_args, str):
            try:
                tool_args = json.loads(raw_args)
            except json.JSONDecodeError:
                tool_args = {}
        elif isinstance(raw_args, dict):
            tool_args = dict(raw_args)
        else:
            tool_args = {}

        narrative = ""
        if isinstance(tool_args, dict) and "narrative" in tool_args:
            narrative = str(tool_args.get("narrative", ""))

        return tool_name, tool_args, narrative, tool_call_id

    def _normalize_tool_calls(self, tool_calls: list[Any]) -> list[ToolCall]:
        normalized: list[ToolCall] = []
        for call in tool_calls or []:
            if isinstance(call, ToolCall):
                normalized.append(call)
                continue
            if isinstance(call, dict):
                func = call.get("function") or {}
                name = call.get("name") or func.get("name") or ""
                arguments = func.get("arguments") or call.get("arguments") or call.get("input") or {}
                call_id = call.get("id") or str(uuid4())
                normalized.append(ToolCall(id=call_id, function=Function.create(name, arguments)))
                continue
            name = getattr(call, "name", "") or getattr(getattr(call, "function", None), "name", "")
            arguments = getattr(call, "arguments", None) or getattr(getattr(call, "function", None), "arguments", None) or {}
            call_id = getattr(call, "id", None) or str(uuid4())
            normalized.append(ToolCall(id=call_id, function=Function.create(name, arguments)))
        return normalized

    async def _execute_tool(self, tool_name: str, tool_args: dict) -> str:
        """Execute tool by name and return result text."""
        tool = None
        if hasattr(self.available_tools, "get_tool"):
            tool = self.available_tools.get_tool(tool_name)
        elif hasattr(self.available_tools, "tools"):
            for candidate in self.available_tools.tools:
                if getattr(candidate, "name", "") == tool_name:
                    tool = candidate
                    break

        if tool is None:
            return f"Tool not available: {tool_name}"

        try:
            result = tool.execute(**tool_args)
            if hasattr(result, "__await__"):
                result = await result
            return str(result)
        except Exception as exc:
            return f"Tool error: {exc}"

    def _summarize_tool_result(self, tool_result: str, limit: int = 200) -> str:
        """Short summary for tool action log."""
        if not tool_result:
            return ""
        if len(tool_result) <= limit:
            return tool_result
        return tool_result[:limit].rstrip() + "..."

    def _get_stance_label(self) -> str:
        """Return a vague stance label (player-facing)."""
        if self.stance_value > 80:
            return "Strongly favors guilty"
        elif self.stance_value > 60:
            return "Leans guilty"
        elif self.stance_value > 40:
            return "Undecided"
        elif self.stance_value > 20:
            return "Leans not guilty"
        else:
            return "Strongly favors not guilty"

    def get_final_vote(self) -> bool:
        """Final vote: True = guilty, False = not guilty."""
        if self.last_vote is not None:
            return bool(self.last_vote)
        return self.stance_value > 50

    def get_first_message(self) -> str:
        """Return juror opening line."""
        return self.juror_config.first_message if self.juror_config else ""

    def get_info(self) -> dict:
        """Return basic juror info."""
        return {
            "id": self.juror_id,
            "name": self.juror_config.name if self.juror_config else "",
            "codename": self.juror_config.codename if self.juror_config else "",
            "stance_label": self._get_stance_label(),
            "occupation": self.juror_config.occupation if self.juror_config else "",
            "portrait": self.juror_config.portrait if self.juror_config else "",
        }

    def reset(self) -> None:
        """Reset agent state for a new game."""
        self.conversation_history = []
        if self.juror_config:
            self.stance_value = max(0, min(100, self.juror_config.initial_stance))
        self.last_vote = None
        self.memory.clear()
        self.state = AgentState.IDLE
        self.current_step = 0

    # Compatibility property
    @property
    def config(self) -> Optional[JurorConfig]:
        """Compatibility alias for JurorAgent-style config."""
        return self.juror_config
