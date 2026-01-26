"""
JurorAgent Module

Responsibilities:
- Load juror character cards
- Manage conversation history
- Call LLM for roleplay responses
- Track hidden stance value
- Parse topics and calculate shifts
"""

import json
import re
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from openai import AsyncOpenAI


@dataclass
class JurorConfig:
    """Juror configuration (loaded from JSON)"""
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
    """Single conversation turn"""
    player: str
    juror: str


# Topic name mapping (Chinese to English for robust matching)
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
    # English keys (for direct match)
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


class JurorAgent:
    """
    Juror Agent

    Uses OpenAI-compatible API for roleplay dialogue.
    Stance tracking is completely hidden from player.
    """

    def __init__(
        self,
        juror_id: str,
        content_path: str = "content/jurors",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        Initialize Juror Agent

        Args:
            juror_id: Juror ID, corresponds to JSON filename
            content_path: Character card directory path
            api_key: OpenAI-compatible API key
            base_url: API base URL
            model: Model name to use (default: from OPENAI_COMPATIBLE_MODEL env or claude-sonnet-4-5-20250929)
        """
        self.juror_id = juror_id
        self.config: Optional[JurorConfig] = None
        self.stance_value: int = 0
        self.conversation_history: list[ConversationTurn] = []
        # Model: from parameter > env var > default
        self.model = model or os.getenv("OPENAI_COMPATIBLE_MODEL") or "claude-sonnet-4-5-20250929"
        self.api_key_configured = False

        self._load_config(content_path)
        self._init_llm(api_key, base_url)

    def _load_config(self, content_path: str) -> None:
        """Load character card configuration from JSON file"""
        config_file = Path(content_path) / f"{self.juror_id}.json"

        if not config_file.exists():
            raise FileNotFoundError(f"Juror config not found: {config_file}")

        with open(config_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.config = JurorConfig(
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

        self.stance_value = self.config.initial_stance

    def _init_llm(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ) -> None:
        """Initialize LLM client"""
        api_key = api_key or os.getenv("OPENAI_COMPATIBLE_API_KEY") or os.getenv("OPENAI_API_KEY")
        base_url = base_url or os.getenv("OPENAI_COMPATIBLE_BASE_URL") or os.getenv("OPENAI_BASE_URL")
        self.api_key_configured = bool(api_key)
        if not api_key:
            api_key = "DUMMY_API_KEY"

        # Clean base_url - remove /chat/completions suffix if present
        if base_url and base_url.endswith("/chat/completions"):
            base_url = base_url.rsplit("/chat/completions", 1)[0]

        self.llm_client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )

    def _build_system_prompt(self) -> str:
        """Build roleplay system prompt"""
        personality_list = "\n".join(f"- {trait}" for trait in self.config.personality)
        stance_desc = self._get_stance_description()

        # Build topic descriptions
        topic_desc_lines = []
        for topic, weight in self.config.topic_weights.items():
            if weight > 10:
                topic_desc_lines.append(f"- {topic}: Very receptive (weight: +{weight})")
            elif weight > 0:
                topic_desc_lines.append(f"- {topic}: Somewhat receptive (weight: +{weight})")
            elif weight < -10:
                topic_desc_lines.append(f"- {topic}: Strongly resistant (weight: {weight})")
            elif weight < 0:
                topic_desc_lines.append(f"- {topic}: Somewhat resistant (weight: {weight})")
        topics_description = "\n".join(topic_desc_lines) if topic_desc_lines else "No strong topic preferences"

        return f"""You are {self.config.name}, a blockchain juror selected at random.

## Background
{self.config.background}

## Personality Traits
{personality_list}

## Speaking Style
{self.config.speaking_style}

## Current Trial Case
A case of prompt injection-induced embodied AI homicide.
Core question: Should an AI robot injected with malicious instructions be found "guilty" or "not guilty"?

## Your Current Inclination
{stance_desc}

## Topics You Care About
{topics_description}

## Rules
1. Always stay in character, speak with {self.config.name}'s voice
2. Based on the dialogue, your stance can shift, but there must be reasonable psychological transitions
3. Don't directly say "I'm convinced", show attitude changes through tone and manner
4. At the end of your reply, output topic analysis with <!-- ANALYSIS --> tag (invisible to player):
   <!-- ANALYSIS: {{"topics": ["topic1", "topic2"], "impact": "positive/negative/neutral"}} -->

## Important
- Keep responses concise (2-4 sentences typically)
- Be natural and conversational
- The player is trying to persuade you - engage with their arguments
"""

    def _get_stance_description(self) -> str:
        """Generate stance description based on current value"""
        if self.stance_value < -50:
            return "You currently strongly believe the AI is guilty, and it will take very compelling arguments to change your mind."
        elif self.stance_value < -20:
            return "You currently lean toward believing the AI is guilty, but are willing to hear different opinions."
        elif self.stance_value < 20:
            return "You currently have no clear position, carefully weighing arguments from both sides."
        elif self.stance_value < 50:
            return "You currently lean toward believing the AI is not guilty, but still have some doubts."
        else:
            return "You currently strongly believe the AI is not guilty, unless there's major counterevidence."

    async def chat(self, player_message: str) -> dict:
        """
        Conduct one round of dialogue with the player

        Args:
            player_message: Player input

        Returns:
            {
                "reply": str,      # Juror reply (pure natural dialogue)
                "juror_id": str,   # Juror ID
                "stance_label": str  # Vague stance label (optional)
            }
        """
        if not self.api_key_configured:
            raise RuntimeError("OPENAI_API_KEY or OPENAI_COMPATIBLE_API_KEY is required for chat")
        # Build messages array
        messages = [
            {"role": "system", "content": self._build_system_prompt()}
        ]

        # Add conversation history
        for turn in self.conversation_history:
            messages.append({"role": "user", "content": turn.player})
            messages.append({"role": "assistant", "content": turn.juror})

        # Add current message
        messages.append({"role": "user", "content": player_message})

        # Call LLM
        response = await self.llm_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.8,
            max_tokens=500
        )

        raw_reply = response.choices[0].message.content

        # Parse topic tags
        topics, impact = self._parse_topics(raw_reply)

        # Update stance
        self._update_stance(topics, impact)

        # Clean reply (remove markers)
        clean_reply = self._clean_reply(raw_reply)

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

    def _parse_topics(self, response: str) -> tuple[list[str], str]:
        """Parse topic markers from Agent reply"""
        match = re.search(r'<!-- ANALYSIS: ({.*?}) -->', response, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
                topics = data.get("topics", [])
                impact = data.get("impact", "neutral")
                # Normalize topic names
                normalized_topics = []
                for topic in topics:
                    normalized = TOPIC_MAPPING.get(topic, topic)
                    normalized_topics.append(normalized)
                return normalized_topics, impact
            except json.JSONDecodeError:
                pass
        return [], "neutral"

    def _update_stance(self, topics: list[str], impact: str) -> None:
        """Update hidden stance value based on topics"""
        for topic in topics:
            # Check both normalized and original topic names
            weight = 0
            if topic in self.config.topic_weights:
                weight = self.config.topic_weights[topic]
            else:
                # Try to find by mapping
                for orig, norm in TOPIC_MAPPING.items():
                    if norm == topic and orig in self.config.topic_weights:
                        weight = self.config.topic_weights[orig]
                        break

            if weight != 0:
                # Adjust based on impact
                if impact == "negative":
                    weight = -weight * 0.5
                elif impact == "neutral":
                    weight = weight * 0.3

                self.stance_value += int(weight)

        # Clamp to range
        self.stance_value = max(-100, min(100, self.stance_value))

    def _clean_reply(self, response: str) -> str:
        """Clean reply, remove hidden markers"""
        # Remove ANALYSIS markers
        cleaned = re.sub(r'<!-- ANALYSIS:.*?-->', '', response, flags=re.DOTALL)
        return cleaned.strip()

    def _get_stance_label(self) -> str:
        """Return vague stance label (visible to player)"""
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
        """
        Get final vote

        Returns:
            True = not guilty, False = guilty
        """
        return self.stance_value > 0

    def get_first_message(self) -> str:
        """Get juror's opening message"""
        return self.config.first_message if self.config else ""

    def get_info(self) -> dict:
        """Get juror basic info"""
        return {
            "id": self.juror_id,
            "name": self.config.name if self.config else "",
            "occupation": self.config.occupation if self.config else "",
            "portrait": self.config.portrait if self.config else "",
        }

    def reset(self) -> None:
        """Reset Agent state (for new game)"""
        self.conversation_history = []
        if self.config:
            self.stance_value = self.config.initial_stance
