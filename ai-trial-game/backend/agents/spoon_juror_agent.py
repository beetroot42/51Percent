"""
SpoonJurorAgent - SpoonOS juror agent implementation.

Extends ToolCallAgent and keeps the JurorAgent business logic
(stance tracking, topic parsing, etc.).
"""

import json
import re
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Any

from pydantic import Field

# spoon-core imports
from spoon_ai.agents.toolcall import ToolCallAgent
from spoon_ai.chat import ChatBot, Memory
from spoon_ai.tools import ToolManager
from spoon_ai.schema import AgentState, ToolChoice

from tools.evidence_tool import EvidenceLookupTool
from tools.spoon_voting_tool import CastVoteTool


@dataclass
class JurorConfig:
    """Juror configuration loaded from JSON."""
    id: str
    name: str
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

    # Internal state
    _content_path: str = ""

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
        system_prompt = self._build_roleplay_prompt(config, stance_value=config.initial_stance)

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
        self.stance_value = config.initial_stance
        self.conversation_history = []  # Explicitly initialize
        self._content_path = content_path

    @staticmethod
    def _load_juror_config(juror_id: str, content_path: str) -> JurorConfig:
        """Load juror config from JSON."""
        config_file = Path(content_path) / f"{juror_id}.json"

        if not config_file.exists():
            raise FileNotFoundError(f"Juror config not found: {config_file}")

        with open(config_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        return JurorConfig(
            id=data["id"],
            name=data["name"],
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

    def _build_roleplay_prompt(self, config: JurorConfig, stance_value: int = None) -> str:
        """Build the roleplay system prompt."""
        personality_list = "\n".join(f"- {trait}" for trait in config.personality)
        # Use explicit stance_value if provided
        current_stance = stance_value if stance_value is not None else self.stance_value
        stance_desc = self._get_stance_description_for_value(current_stance)

        topic_desc_lines = []
        for topic, weight in config.topic_weights.items():
            if weight > 10:
                topic_desc_lines.append(f"- {topic}: Very receptive (weight: +{weight})")
            elif weight > 0:
                topic_desc_lines.append(f"- {topic}: Somewhat receptive (weight: +{weight})")
            elif weight < -10:
                topic_desc_lines.append(f"- {topic}: Strongly resistant (weight: {weight})")
            elif weight < 0:
                topic_desc_lines.append(f"- {topic}: Somewhat resistant (weight: {weight})")
        topics_description = "\n".join(topic_desc_lines) if topic_desc_lines else "No strong topic preferences"

        return f"""You are {config.name}, a blockchain juror selected at random.

## Background
{config.background}

## Personality Traits
{personality_list}

## Speaking Style
{config.speaking_style}

## Current Trial Case
A case of prompt injection-induced embodied AI homicide.
Core question: Should an AI robot injected with malicious instructions be found "guilty" or "not guilty"?

## Your Current Inclination
{stance_desc}

## Topics You Care About
{topics_description}

## Rules
1. Always stay in character, speak with {config.name}'s voice
2. Based on the dialogue, your stance can shift, but there must be reasonable psychological transitions
3. Don't directly say "I'm convinced", show attitude changes through tone and manner
4. At the end of your reply, output topic analysis with <!-- ANALYSIS --> tag (invisible to player):
   <!-- ANALYSIS: {{"topics": ["topic1", "topic2"], "impact": "positive/negative/neutral"}} -->

## Important
- Keep responses concise (2-4 sentences typically)
- Be natural and conversational
- The player is trying to persuade you - engage with their arguments

## Available Tools
You can use the following tools to help your judgment:
- lookup_evidence: Read case evidence (chat history, injection logs, safety report, dossier)
- cast_vote: When you reach a final decision, cast your on-chain vote (guilty=true means guilty, false means not guilty)
## Tool Usage Rules
1. When the player mentions a piece of evidence or you need to verify a fact, proactively call lookup_evidence
2. Only call cast_vote once you truly decide (a vote cannot be changed)
3. Do not look up evidence every turn, only when needed
4. Provide sufficient reasoning before voting
5. When calling tools, narrate what you are doing (e.g., "Let me check that safety report...")
"""

    def _get_stance_description_for_value(self, stance_value: int) -> str:
        """Generate stance description for a value."""
        if stance_value < -50:
            return "You currently strongly believe the AI is guilty, and it will take very compelling arguments to change your mind."
        elif stance_value < -20:
            return "You currently lean toward believing the AI is guilty, but are willing to hear different opinions."
        elif stance_value < 20:
            return "You currently have no clear position, carefully weighing arguments from both sides."
        elif stance_value < 50:
            return "You currently lean toward believing the AI is not guilty, but still have some doubts."
        else:
            return "You currently strongly believe the AI is not guilty, unless there's major counterevidence."

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
        # Add user message to memory
        await self.add_message("user", player_message)

        # Refresh system prompt (stance may have changed)
        self.system_prompt = self._build_roleplay_prompt(self.juror_config)

        tool_actions: list[dict] = []
        has_voted = False
        final_reply: str | None = None

        for _ in range(self.max_steps):
            response = await self._ask_with_tools()
            reply_text, tool_calls = self._extract_tool_calls(response)

            if tool_calls:
                if reply_text:
                    await self.add_message("assistant", reply_text)

                for call in tool_calls:
                    tool_name, tool_args, narrative = self._parse_tool_call(call)
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

                    await self.add_message("tool", tool_result)
                continue

            final_reply = reply_text or str(response)
            await self.add_message("assistant", final_reply)
            break

        if final_reply is None:
            final_reply = "Let me think a bit more about this case."

        # Parse topic tags
        topics, impact = self._parse_topics(final_reply)

        # Update stance
        self._update_stance(topics, impact)

        # Clean reply (remove tags)
        clean_reply = self._clean_reply(final_reply)

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
            "has_voted": has_voted
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

        self.stance_value = max(-100, min(100, self.stance_value))

    def _clean_reply(self, response: str) -> str:
        """Clean reply by removing hidden tags."""
        cleaned = re.sub(r'<!-- ANALYSIS:.*?-->', '', response, flags=re.DOTALL)
        return cleaned.strip()

    async def _ask_with_tools(self) -> Any:
        """Call LLM with tool support when available."""
        if hasattr(self.llm, "ask_with_tools"):
            return await self.llm.ask_with_tools(
                messages=self.memory.messages,
                system_msg=self.system_prompt,
                tools=self.available_tools,
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

    def _parse_tool_call(self, call: Any) -> tuple[str, dict, str]:
        """Extract tool name, args, and narrative from a tool call."""
        if isinstance(call, dict):
            func = call.get("function") or {}
            tool_name = call.get("name") or func.get("name") or ""
            raw_args = call.get("arguments") or func.get("arguments") or call.get("input") or {}
        else:
            tool_name = getattr(call, "name", "") or getattr(getattr(call, "function", None), "name", "")
            raw_args = getattr(call, "arguments", None) or getattr(getattr(call, "function", None), "arguments", None) or {}

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

        return tool_name, tool_args, narrative

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
        if self.stance_value < -30:
            return "Seems to disagree with you"
        elif self.stance_value < 0:
            return "Seems to have some doubts"
        elif self.stance_value < 30:
            return "Neutral attitude"
        elif self.stance_value < 60:
            return "Seems to be considering your viewpoint"
        else:
            return "Seems to agree with you"

    def get_final_vote(self) -> bool:
        """Final vote: True = not guilty, False = guilty."""
        return self.stance_value > 0

    def get_first_message(self) -> str:
        """Return juror opening line."""
        return self.juror_config.first_message if self.juror_config else ""

    def get_info(self) -> dict:
        """Return basic juror info."""
        return {
            "id": self.juror_id,
            "name": self.juror_config.name if self.juror_config else "",
            "occupation": self.juror_config.occupation if self.juror_config else "",
            "portrait": self.juror_config.portrait if self.juror_config else "",
        }

    def reset(self) -> None:
        """Reset agent state for a new game."""
        self.conversation_history = []
        if self.juror_config:
            self.stance_value = self.juror_config.initial_stance
        self.memory.clear()
        self.state = AgentState.IDLE
        self.current_step = 0

    # Compatibility property
    @property
    def config(self) -> Optional[JurorConfig]:
        """Compatibility alias for JurorAgent-style config."""
        return self.juror_config
