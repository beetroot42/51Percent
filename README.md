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

## API Highlights

```
POST /chat/{juror_id}?session_id=...     # Dialogue with juror
POST /juror/{id}/present/{evidence_id}   # Show evidence
POST /vote                                # Trigger on-chain voting
GET  /story/ending?verdict=...           # Get narrative ending
```

Full API reference: 40+ endpoints documented in source.
