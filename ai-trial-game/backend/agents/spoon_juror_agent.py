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
    tool_choices: Any = Field(default=ToolChoice.NONE)  # No tool calls in dialogue mode
    max_steps: int = Field(default=1)  # Single turn per chat

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

        # Initialize base agent
        super().__init__(
            name=f"juror_{juror_id}",
            description=f"Juror {config.name}",
            system_prompt=system_prompt,
            llm=llm,
            memory=Memory(),
            available_tools=ToolManager([]),
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
                "stance_label": str
            }
        """
        # Add user message to memory
        await self.add_message("user", player_message)

        # Refresh system prompt (stance may have changed)
        self.system_prompt = self._build_roleplay_prompt(self.juror_config)

        # Call LLM
        response = await self.llm.ask(
            messages=self.memory.messages,
            system_msg=self.system_prompt
        )

        # Add assistant reply
        await self.add_message("assistant", response)

        # Parse topic tags
        topics, impact = self._parse_topics(response)

        # Update stance
        self._update_stance(topics, impact)

        # Clean reply (remove tags)
        clean_reply = self._clean_reply(response)

        # Record conversation history
        self.conversation_history.append(ConversationTurn(
            player=player_message,
            juror=clean_reply
        ))

        return {
            "reply": clean_reply,
            "juror_id": self.juror_id,
            "stance_label": self._get_stance_label()
        }

    async def think(self) -> bool:
        """
        Think step: dialogue only, no tools.

        Overrides base method to disable tool selection.
        """
        # Dialogue mode does not require tools
        return False

    async def act(self) -> str:
        """Dialogue mode does not execute actions."""
        return ""

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
