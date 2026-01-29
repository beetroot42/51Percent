# AI Trial (AI Trial Game)

AI Trial is a blockchain jury persuasion game. The player investigates a case, then persuades jurors, and finally triggers an on-chain vote.

Note: Player-facing narrative content (dossier, evidence, witnesses, jurors) is stored in `content/` and remains in Chinese.

## Requirements

- Python 3.10+
- Optional: Foundry/Anvil for on-chain voting
- Optional: LLM API for juror chat

## Python Environment Setup

Use a local venv and always run commands with the venv Python.

```bash
python -m venv venv
venv\\Scripts\\activate
python -m pip install -r backend/requirements.txt
```

On macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r backend/requirements.txt
```

## Quick Start

```bash
cd ai-trial-game
python -m venv venv
venv\\Scripts\\activate
python -m pip install -r backend/requirements.txt
copy backend/.env.example backend/.env
python start.py
```

Open:
- http://localhost:8080/game (or `SERVER_PORT` from `.env`)

## Environment Verification

- Run the built-in checks: `python start.py`
- Verify spoon-core import (venv Python): `python -c "import spoon_ai; print('spoon-core OK')"`

## Manual Start

```bash
cd ai-trial-game
venv\\Scripts\\activate
python -m pip install -r backend/requirements.txt
python backend/main.py
```

## Structure

```
ai-trial-game/
  backend/    FastAPI server and agents
  frontend/   HTML/CSS/JS UI
  content/    Game narrative data (Chinese)
  contracts/  Solidity contract
```

## Troubleshooting

See `TROUBLESHOOTING.md` for voting stalls, spoon-core import errors, and port conflicts.

---

## Changelog

### v0.2.0 - ReAct Agent Upgrade (2026-01-29)

Upgraded `SpoonJurorAgent` from dialog-only to full ReAct (Reason-Act) pattern with tool calling.

**New Features:**
- **Evidence Lookup Tool** (`lookup_evidence`) - Agents can autonomously retrieve case evidence
- **On-chain Voting Tool** (`cast_vote`) - Agents can cast blockchain votes during dialogue
- **Tool Action Visualization** - Frontend displays agent tool usage narratively

**Backend Changes:**
- `backend/tools/evidence_tool.py` - New `EvidenceLookupTool`
- `backend/agents/spoon_juror_agent.py` - ReAct loop with `tool_choices=AUTO`, `max_steps=3`
- `backend/services/agent_manager.py` - Voting config injection with `juror_index`
- `backend/main.py` - New `ToolAction` model, `tool_actions`/`has_voted` in API response

**Frontend Changes:**
- `frontend/js/game.js` - Tool action rendering with XSS protection

**Tests:**
- `backend/tests/test_evidence_tool.py` - Evidence tool unit tests
- `backend/tests/test_react_agent.py` - ReAct loop and AgentManager tests

**Reports:**
- `REPORT_REACT_BACKEND.md` - Backend implementation details
- `REPORT_REACT_VISUALIZATION.md` - Frontend visualization details

### v0.1.0 - Initial Release

- Three-phase gameplay: Investigation → Persuasion → Verdict
- 5 AI jurors with personality-driven dialogue
- On-chain voting via Solidity contract
- spoon-core framework integration
