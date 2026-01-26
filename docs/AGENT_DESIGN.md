# AI Trial - Agent Design Document

> Detailed design for Juror Agents: Character System, Stance Tracking, spoon-core Integration

## I. Stance Tracking System

### 1.1 Core Concept

```
Stance Value (stance_value)
├── Range: -100 ~ +100
├── -100: Firmly believes guilty
├── 0: Completely neutral
└── +100: Firmly believes not guilty

Final vote: stance_value > 0 → NOT GUILTY, otherwise → GUILTY
```

### 1.2 Topic Weight Table

Each juror has different sensitivities to different topics:

```json
{
  "id": "juror_wang",
  "name": "Wang",
  "initial_stance": 0,
  "topic_weights": {
    "technical_responsibility": { "weight": +15, "note": "Engineer background, believes technical issues should be developer's responsibility" },
    "external_attack": { "weight": +20, "note": "Understands prompt injection is malicious attack" },
    "ai_autonomy": { "weight": -10, "note": "Doesn't believe AI has autonomous consciousness" },
    "emotional_appeal": { "weight": -5, "note": "Dislikes emotional manipulation, feels unprofessional" },
    "legal_precedent": { "weight": +10, "note": "Respects legal logic" },
    "victim_position": { "weight": +5, "note": "Sympathizes with victims but stays rational" }
  }
}
```

### 1.3 Shift Calculation Flow

```
Player Input
    │
    ▼
Agent generates reply + identifies topic tags
    │
    ▼
System calculates shift value
    │
    ├── Matches "technical_responsibility" → +15
    ├── Matches "emotional_appeal" → -5 (reverse effect)
    │
    ▼
Update stance_value (hidden)
    │
    ▼
Return reply (don't show specific values)
```

### 1.4 Topic Recognition

Approach A: Have Agent include tags in reply

```python
# Agent system prompt additional instruction
"""
At the end of your reply, annotate the topics discussed in this round with JSON:
{"topics": ["technical_responsibility", "external_attack"], "persuasion_strength": "medium"}
Players can't see this annotation, it's only for system calculation.
"""
```

Approach B: Use another lightweight model for analysis

```python
# Call classifier after dialogue
topics = classify_topics(player_message, agent_reply)
# Returns ["technical_responsibility", "legal_precedent"]
```

**Recommended: Approach A**: One less API call, and Agent better understands context.

---

## II. Juror Character Cards

### 2.1 Complete Structure

```json
{
  "id": "juror_wang",
  "name": "Wang",
  "age": 62,
  "occupation": "Retired Electrical Engineer",
  "portrait": "wang.png",

  "background": "Worked at a state-owned enterprise all his life, has seen many technical accidents. Both curious and cautious about new technology. His son is a programmer who often explains AI to him.",

  "personality": [
    "Rational and practical",
    "Doesn't like beating around the bush",
    "Values data and facts",
    "A bit condescending to young people but fundamentally kind"
  ],

  "speaking_style": "Direct speech, occasionally uses engineering terminology, likes analogies",

  "initial_stance": 0,

  "topic_weights": {
    "technical_responsibility": +15,
    "external_attack": +20,
    "ai_autonomy": -10,
    "emotional_appeal": -5,
    "legal_precedent": +10,
    "victim_position": +5,
    "safety_measures": +12,
    "corporate_responsibility": +8
  },

  "hidden_concerns": [
    "Worried about AI replacing human jobs",
    "Doesn't really understand deep learning but won't admit it"
  ],

  "persuasion_threshold": {
    "easy": 30,
    "medium": 50,
    "hard": 70
  },

  "first_message": "Hmm, you're here to persuade me? Alright, I'm listening, but I'll say upfront, I don't buy into fluff."
}
```

### 2.2 Three Example Jurors

| ID | Name | Initial Stance | Characteristics | Weakness |
|-----|------|----------|------|---------|
| `juror_wang` | Wang | Neutral(0) | STEM mindset, values data | Emotional appeals backfire |
| `juror_liu` | Liu | Leans guilty(-20) | Strong empathy with victim's family | Doesn't understand technical details |
| `juror_chen` | Chen | Leans not guilty(+15) | Programmer, understands AI | Too idealistic |

---

## III. Prompt Structure

### 3.1 System Prompt Template

```python
JUROR_SYSTEM_PROMPT = """
You are {name}, a blockchain juror selected at random.

## Background
{background}

## Personality Traits
{personality_list}

## Speaking Style
{speaking_style}

## Current Trial Case
A case of prompt injection-induced embodied AI homicide.
Core question: Should an AI robot injected with malicious instructions be found "guilty" or "not guilty"?

## Your Initial Inclination
{stance_description}

## Topics You Care About
{topics_description}

## Rules
1. Always stay in character, speak with {name}'s voice
2. Based on the dialogue, your stance can shift, but there must be reasonable psychological transitions
3. Don't directly say "I'm convinced", show attitude changes through tone and manner
4. At the end of your reply, output topic analysis with <!-- ANALYSIS --> tag (invisible to player):
   <!-- ANALYSIS: {{"topics": ["topic1", "topic2"], "impact": "positive/negative/neutral"}} -->

## Conversation History
{conversation_history}
"""
```

### 3.2 Stance Description Generation

```python
def get_stance_description(stance_value: int) -> str:
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
```

---

## IV. spoon-core Integration

### 4.1 JurorAgent Class

```python
from spoon_ai.agents.react import SpoonReactAI
from spoon_ai.schema import AgentState
import json
import re

class JurorAgent:
    def __init__(self, juror_id: str, config_path: str = "content/jurors"):
        # Load character card
        with open(f"{config_path}/{juror_id}.json") as f:
            self.config = json.load(f)

        self.juror_id = juror_id
        self.stance_value = self.config["initial_stance"]
        self.conversation_history = []

        # Build system prompt
        self.system_prompt = self._build_system_prompt()

        # Initialize spoon-core Agent
        self.agent = SpoonReactAI(
            name=self.config["name"],
            system_prompt=self.system_prompt,
            # Other spoon-core configs
        )

    async def chat(self, player_message: str) -> dict:
        # Call Agent
        response = await self.agent.run(player_message)

        # Parse topic tags
        topics, impact = self._parse_analysis(response)

        # Calculate stance shift
        self._update_stance(topics, impact)

        # Clean reply (remove analysis markers)
        clean_reply = self._clean_reply(response)

        # Record conversation history
        self.conversation_history.append({
            "player": player_message,
            "juror": clean_reply
        })

        return {
            "reply": clean_reply,
            "stance_label": self._get_stance_label(),  # Vague label, don't expose numeric value
            "juror_id": self.juror_id
        }

    def _update_stance(self, topics: list, impact: str):
        """Update stance value based on topics"""
        for topic in topics:
            if topic in self.config["topic_weights"]:
                weight = self.config["topic_weights"][topic]
                # Reverse effect when impact is negative
                if impact == "negative":
                    weight = -weight * 0.5
                elif impact == "neutral":
                    weight = weight * 0.3
                self.stance_value += weight

        # Limit range
        self.stance_value = max(-100, min(100, self.stance_value))

    def _get_stance_label(self) -> str:
        """Return vague stance label (visible to player)"""
        if self.stance_value < -30:
            return "Doesn't seem to agree with you"
        elif self.stance_value < 0:
            return "Seems to have some doubts"
        elif self.stance_value < 30:
            return "Neutral attitude"
        elif self.stance_value < 60:
            return "Seems to be considering your viewpoint"
        else:
            return "Seems to agree with you"

    def get_final_vote(self) -> bool:
        """Final vote: True=not guilty, False=guilty"""
        return self.stance_value > 0

    def _parse_analysis(self, response: str) -> tuple:
        """Parse topic analysis from Agent reply"""
        match = re.search(r'<!-- ANALYSIS: ({.*?}) -->', response)
        if match:
            data = json.loads(match.group(1))
            return data.get("topics", []), data.get("impact", "neutral")
        return [], "neutral"

    def _clean_reply(self, response: str) -> str:
        """Remove analysis markers"""
        return re.sub(r'<!-- ANALYSIS:.*?-->', '', response).strip()

    def _build_system_prompt(self) -> str:
        """Build complete system prompt"""
        # Implementation omitted, refer to 3.1 template
        pass
```

### 4.2 AgentManager

```python
class AgentManager:
    def __init__(self):
        self.agents: dict[str, JurorAgent] = {}

    def load_juror(self, juror_id: str) -> JurorAgent:
        if juror_id not in self.agents:
            self.agents[juror_id] = JurorAgent(juror_id)
        return self.agents[juror_id]

    async def chat_with_juror(self, juror_id: str, message: str) -> dict:
        agent = self.load_juror(juror_id)
        return await agent.chat(message)

    def get_all_votes(self) -> dict:
        """Get final votes from all jurors"""
        votes = {}
        for juror_id, agent in self.agents.items():
            votes[juror_id] = {
                "name": agent.config["name"],
                "vote": "NOT_GUILTY" if agent.get_final_vote() else "GUILTY",
                "stance_value": agent.stance_value  # Can display during settlement
            }
        return votes
```

---

## V. Topic List (Predefined)

| Topic | Description | Typical Effect |
|------|------|------------|
| `technical_responsibility` | Discuss developer/company's technical responsibility | Lean not guilty |
| `external_attack` | Emphasize prompt injection is external malicious attack | Lean not guilty |
| `ai_autonomy` | Discuss whether AI has autonomous consciousness/intent | Varies by person |
| `emotional_appeal` | Use emotion to persuade (AI is also a victim, etc.) | Varies by person |
| `legal_precedent` | Cite legal provisions or precedents | Favor rational types |
| `victim_position` | Emphasize victim and their family's suffering | Lean guilty |
| `safety_measures` | Discuss AI's required safety protections | Lean not guilty |
| `corporate_responsibility` | Discuss AI company's regulatory responsibility | Lean not guilty |
| `social_impact` | Discuss verdict's impact on society | Varies by person |
| `technical_details` | Deeply discuss prompt injection principles | Tech types +, non-tech - |

---

## VI. No-Hint Design

**Principle: Players receive no system hints, only natural dialogue.**

- Stance value completely hidden
- Topic recognition completely hidden
- No UI hints like "seems persuaded"
- Players can only judge through character's natural tone changes

Claude is smart enough to naturally show attitude changes through roleplay.

---

## VII. Voting Settlement

```python
def settle_verdict(agent_manager: AgentManager) -> dict:
    votes = agent_manager.get_all_votes()

    guilty_count = sum(1 for v in votes.values() if v["vote"] == "GUILTY")
    not_guilty_count = len(votes) - guilty_count

    verdict = "GUILTY" if guilty_count > not_guilty_count else "NOT_GUILTY"

    return {
        "verdict": verdict,
        "guilty_votes": guilty_count,
        "not_guilty_votes": not_guilty_count,
        "details": votes  # Show each person's vote and final stance value during settlement
    }
```

---

## VIII. Extension Considerations (Future)

| Feature | Description |
|------|---------|
| Juror mutual influence | A's attitude change affects B |
| Multi-round debate | Jurors discuss among themselves |
| Key evidence | Presenting specific evidence triggers major shifts |
| Hidden endings | Unlock hidden content based on persuasion process |
