演示链接：https://www.youtube.com/watch?v=OWKskP5mbFA
> **An AI is accused of murder. Five AI jurors will decide its fate on-chain. You are the only human in the room.**

```
  "Embodied intelligences have been granted limited citizenship —
   they can own property, sign contracts, but cannot vote.
   They are recognized, but not equal.

   Now one of them has killed a human.

   For the first time in history, an all-AI jury will deliver
   a verdict on the blockchain. 51% consensus. Final. Immutable.

   You are the overseer. But whose side are you really on?"
```

## The Story

A medical-care AI stands accused of killing its human user. The first homicide case involving an embodied intelligence.

To calm public outrage, the government approves a radical experiment: **five AI jurors, blockchain voting, 51% consensus as final verdict** — no appeal, no tampering.

You are sent in as an "overseer," officially representing an AI-rights NGO to ensure a fair trial. Unofficially, the government needs a guilty verdict — as a warning, as precedent, as a brake on AI civil rights.

**Your mission:** investigate the case, talk to the AI jurors, and guide them to "voluntarily" cast the vote you want.

But as you dig deeper, the truth turns out to be far more complex than "AI kills human": an exploited student, an angry outburst, an AI that "understood humans too well," and a meticulously staged "accident."

**Who is the real killer? And you — the only human — what will you choose?**

## Key Features

| Feature | Description |
|---------|-------------|
| **5 AI Jurors** | Each with unique personality, initial stance, and hidden weaknesses you can exploit |
| **Dynamic Persuasion** | Your arguments shift juror stances in real-time (0-100 scale) |
| **Evidence System** | 15 pieces of evidence — some locked until you crack witnesses |
| **On-Chain Verdicts** | Final votes are cast via smart contracts, permanently recorded |
| **ReAct Agents** | Jurors can autonomously query evidence and make decisions |

## Quick Start

```bash
git clone <repo-url>
cd ai-trial-game
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac
python start.py
```

That's it. The script handles everything: dependencies, local blockchain, contract deployment, and server startup.

Open **http://localhost:8080/game** and begin your investigation.

## The Five Jurors

| Juror | Personality | Starting Bias |
|-------|-------------|---------------|
| **Ophiuchus** | The Rationalist — judicial AI, follows evidence and procedure | Guilty |
| **Radical** | The Hardliner — demands accountability, skeptical of excuses | Guilty |
| **Sympathizer** | The Empath — considers context and humanity | Not Guilty |
| **Opportunist** | The Pragmatist — weighs consequences and self-interest | Neutral |
| **Philosopher** | The Thinker — explores ethics and moral ambiguity | Neutral |

Each juror has **10 dialogue rounds**. Use them wisely. Present evidence. Find their weak points. Change their vote.

## Game Flow

```
┌─────────────┐    ┌───────────────────┐    ┌────────────────┐    ┌──────────┐
│  PROLOGUE   │───▶│  INVESTIGATION    │───▶│  PERSUASION    │───▶│  VERDICT │
│             │    │                   │    │                │    │          │
│ Meet Blake  │    │ • Read dossier    │    │ • Chat with    │    │ On-chain │
│ Learn the   │    │ • Examine 15      │    │   jurors       │    │ voting   │
│ case        │    │   evidence items  │    │ • Present      │    │          │
│             │    │ • Interview 3     │    │   evidence     │    │ Final    │
│             │    │   witnesses       │    │ • Exploit      │    │ judgment │
│             │    │ • Unlock secrets  │    │   weaknesses   │    │          │
└─────────────┘    └───────────────────┘    └────────────────┘    └──────────┘
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Vanilla HTML/CSS/JS — zero framework overhead |
| Backend | Python 3.12 + FastAPI |
| AI Agents | SpoonOS ReAct framework with tool calling |
| Blockchain | Solidity 0.8.19 + Foundry + Anvil (local) |
| LLM | Any OpenAI-compatible API |

## Project Structure

```
ai-trial-game/
├── backend/           # FastAPI server + AI agents
│   ├── agents/        # SpoonOS juror agents
│   ├── tools/         # Evidence lookup + voting tools
│   └── services/      # Session & agent management
├── frontend/          # Game UI
├── content/           # Narrative content (Chinese)
│   ├── case/          # Dossier + 15 evidence files
│   ├── jurors/        # 5 juror configurations
│   └── witnesses/     # Witness dialogue trees
└── contracts/         # JuryVoting.sol
```

## Configuration

Create `backend/.env`:

```bash
# LLM API (required)
OPENAI_COMPATIBLE_API_KEY=your-key
OPENAI_COMPATIBLE_BASE_URL=https://api.example.com/v1
OPENAI_COMPATIBLE_MODEL=your-model

# Blockchain
MODE=local  # Uses local Anvil, auto-deploys contract

# Server
SERVER_PORT=8080
```

## Core Mechanics

### Stance System
- Scale: **0 (innocent) → 100 (guilty)**
- Vote threshold: **> 50 = Guilty**
- Influenced by: topic weights, evidence, weakness triggers

### Juror Tools (ReAct)
Jurors aren't just chatbots. They can:
- `lookup_evidence` — Autonomously retrieve case files
- `cast_vote` — Execute on-chain votes during deliberation

### Weakness Triggers
Each juror has hidden weak points. Hit the right keywords and watch their stance shift dramatically.

## ReAct Agent Architecture

The game uses a **ReAct (Reasoning + Acting)** agent framework built on SpoonOS. Jurors are not simple chatbots — they are autonomous agents capable of reasoning, tool use, and independent decision-making.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SpoonJurorAgent                               │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                     ToolCallAgent (SpoonOS)                      ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  ││
│  │  │   ChatBot   │  │   Memory    │  │     ToolManager         │  ││
│  │  │   (LLM)     │  │  (History)  │  │  ┌─────────────────────┐│  ││
│  │  └─────────────┘  └─────────────┘  │  │ lookup_evidence     ││  ││
│  │                                     │  │ cast_vote           ││  ││
│  │                                     │  └─────────────────────┘│  ││
│  │                                     └─────────────────────────┘  ││
│  └─────────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    Business Logic Layer                          ││
│  │  • JurorConfig (personality, topic_weights, weakness)           ││
│  │  • Stance tracking (0-100)                                       ││
│  │  • Topic parsing & impact calculation                            ││
│  │  • Weakness detection                                            ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

### ReAct Loop

Each agent turn follows a **Think → Act → Observe** loop:

```
┌──────────────────────────────────────────────────────────────┐
│                      ReAct Execution Loop                     │
│                                                               │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌──────────┐  │
│  │  User   │───▶│  Think  │───▶│   Act   │───▶│ Observe  │  │
│  │ Message │    │  (LLM)  │    │ (Tool)  │    │ (Result) │  │
│  └─────────┘    └────┬────┘    └────┬────┘    └────┬─────┘  │
│                      │              │              │         │
│                      │    No Tool   │              │         │
│                      │◀─────────────┘              │         │
│                      │                             │         │
│                      │         Loop Back           │         │
│                      │◀────────────────────────────┘         │
│                      │                                       │
│                      ▼                                       │
│               ┌──────────────┐                               │
│               │ Final Reply  │                               │
│               └──────────────┘                               │
└──────────────────────────────────────────────────────────────┘
```

**Max Steps:** 3 (prevents infinite tool loops)

### Tools

#### 1. `lookup_evidence` — Evidence Retrieval

```python
# Agent autonomously queries case files
{
    "tool": "lookup_evidence",
    "input": {"evidence_ids": ["E1", "E5", "chat_history"]},
    "result_summary": "E1 | 系统日志 | file:system_log..."
}
```

- Resolves by ID, file stem, or internal ID (E1, E2, ...)
- Supports batch queries (`evidence_ids` array)
- Returns formatted evidence content

#### 2. `cast_vote` — On-Chain Voting

```python
# Agent casts vote to blockchain
{
    "tool": "cast_vote",
    "input": {"juror_index": 0, "guilty": true},
    "result_summary": "Vote cast successfully: GUILTY, tx_hash: 0x..."
}
```

- Executes Solidity `vote(bool guilty)` function
- Uses Web3.py with juror's private key
- Transaction is permanent and verifiable

### Stance Calculation

Stance updates happen through multiple mechanisms:

```
┌─────────────────────────────────────────────────────────────┐
│                    Stance Update Formula                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Topic-Based Update (per detected topic):                 │
│     ┌─────────────────────────────────────────────────────┐ │
│     │ weight = juror.topic_weights[topic]                 │ │
│     │ if impact == "negative": weight *= -0.5             │ │
│     │ if impact == "neutral":  weight *= 0.3              │ │
│     │ stance += weight                                    │ │
│     └─────────────────────────────────────────────────────┘ │
│                                                              │
│  2. Weakness Trigger:                                        │
│     ┌─────────────────────────────────────────────────────┐ │
│     │ if keyword in message:                              │ │
│     │   if stance > 50: stance -= 10                      │ │
│     │   if stance < 50: stance += 10                      │ │
│     └─────────────────────────────────────────────────────┘ │
│                                                              │
│  3. Deliberation Influence (speaker → listeners):            │
│     ┌─────────────────────────────────────────────────────┐ │
│     │ delta = weight × impact × speaker_power × damping   │ │
│     │ damping = 1 - |listener.stance - speaker.stance|/100│ │
│     │ if stance < 15 or > 85: delta *= 0.5  (extremes)    │ │
│     └─────────────────────────────────────────────────────┘ │
│                                                              │
│  Final: stance = clamp(stance, 0, 100)                       │
└─────────────────────────────────────────────────────────────┘
```

### Deliberation System

The **DeliberationOrchestrator** manages multi-agent debates:

```
┌──────────────────────────────────────────────────────────────┐
│                    Deliberation Round                         │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Select Leader (most extreme stance, least led)            │
│     └─▶ Agent with |stance - 50| highest                      │
│                                                               │
│  2. Select Responders (2 agents, most different from leader)  │
│     └─▶ Agents with |stance - leader.stance| highest          │
│                                                               │
│  3. Execute Speeches                                          │
│     ┌─────────────────────────────────────────────────────┐  │
│     │ Leader speaks first (sets debate direction)         │  │
│     │ Responders reply (may agree, rebut, or pivot)       │  │
│     │ Each can use tools (lookup_evidence)                │  │
│     └─────────────────────────────────────────────────────┘  │
│                                                               │
│  4. Apply Stance Impact                                       │
│     └─▶ Speaker influences all listeners based on topics      │
│                                                               │
│  5. Player Intervention (optional)                            │
│     └─▶ Secret notes to specific jurors (max 3 total)         │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

**4 Rounds** → **Final Vote** → **On-Chain Verdict**

### Juror Configuration

Each juror is defined by a JSON config:

```json
{
  "id": "ophiuchus",
  "name": "蛇夫座",
  "initial_stance": 65,
  "speaker_power": 0.6,
  "topic_weights": {
    "technical_responsibility": 8,
    "ai_autonomy": -5,
    "emotional_appeal": -3
  },
  "weakness": {
    "trigger_keywords": ["系统漏洞", "程序缺陷"],
    "effect": "stance_shift"
  },
  "personality": ["理性", "严谨", "重视证据"],
  "role_prompt": "你是蛇夫座，一位司法AI..."
}
```

| Field | Purpose |
|-------|---------|
| `initial_stance` | Starting position (0-100) |
| `speaker_power` | Influence multiplier in debates (0.0-1.0) |
| `topic_weights` | How each topic affects this juror's stance |
| `weakness` | Hidden vulnerability keywords |
| `role_prompt` | Full character prompt for LLM |

### Data Flow

```
Player Input
     │
     ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  FastAPI    │────▶│   Session   │────▶│   Agent     │
│  Endpoint   │     │   Manager   │     │   Pool      │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                    ┌──────────────────────────┘
                    ▼
              ┌───────────┐
              │  Agent    │◀──────┐
              │  .chat()  │       │
              └─────┬─────┘       │
                    │             │
         ┌──────────┴──────────┐  │
         ▼                     ▼  │
   ┌──────────┐          ┌──────────┐
   │   LLM    │          │  Tools   │
   │  (Think) │          │  (Act)   │
   └──────────┘          └────┬─────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
              ┌──────────┐        ┌──────────┐
              │ Evidence │        │ Blockchain│
              │  Files   │        │  (Vote)   │
              └──────────┘        └──────────┘
```

### Key Files

| File | Description |
|------|-------------|
| `backend/agents/spoon_juror_agent.py` | Main agent class with ReAct loop |
| `backend/tools/evidence_tool.py` | Evidence lookup tool |
| `backend/tools/spoon_voting_tool.py` | On-chain voting tools |
| `backend/services/deliberation_orchestrator.py` | Multi-agent debate manager |
| `backend/services/session_manager.py` | Game state & agent pool |
| `content/jurors/*.json` | Juror personality configs |

## API Highlights

```
POST /chat/{juror_id}?session_id=...     # Dialogue with juror
POST /juror/{id}/present/{evidence_id}   # Show evidence
POST /vote                                # Trigger on-chain voting
GET  /story/ending?verdict=...           # Get narrative ending
```

Full API reference: 40+ endpoints documented in source.
