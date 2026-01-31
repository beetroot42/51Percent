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

## Runtime & Configuration Notes

**LLM provider (required for juror chat):**
- Configure in `backend/.env` or environment variables.
- Common vars: `LLM_PROVIDER`, `OPENAI_COMPATIBLE_API_KEY`, `OPENAI_COMPATIBLE_BASE_URL`, `OPENAI_COMPATIBLE_MODEL`.
- spoon-core is used for tool calling and chat (`-e ../../spoon-core-main/spoon-core-main` in `backend/requirements.txt`).

**Session-bound APIs (must include `session_id`):**
- `POST /phase/{phase}` — include `?session_id=...` to sync session phase
- `POST /chat/{juror_id}` — includes `?session_id=...`
- `POST /juror/{juror_id}/present/{evidence_id}` — includes `?session_id=...`
- `GET /content/evidence` and `GET /content/evidence/{id}` — include `?session_id=...` for locked evidence

**Persuasion phase limits:**
- Each juror allows **10 dialogue rounds** (chat + evidence presentation both consume a round).
- Round count is tracked per juror per session.

**Evidence IDs:**
- `lookup_evidence` accepts internal IDs (`E1`–`E10`), file stems, or legacy IDs.
- Supports multi-lookup via `evidence_ids` array.

**Voting:**
- `POST /vote` triggers each juror to cast on-chain votes via tools.
- Requires `JURY_VOTING_PRIVATE_KEYS` and contract address configured.

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

## Architecture & Mechanics (Agent-Facing)

### Phase Flow
- **Prologue**: narrative intro + Blake dialogue
- **Investigation**: dossier/evidence/witness interactions (evidence can be locked/unlocked)
- **Persuasion**: juror chat + evidence presentation (per‑juror round limits apply)
- **Verdict**: jurors cast on-chain votes via tool calls

### Session Model
- A `session_id` is created on `/story/opening`.
- Session tracks: phase, unlocked evidence, witness nodes/rounds, juror rounds, initial juror stances.
- Any **session-bound endpoint** must include `session_id` or phase checks will fail.

### Juror Stance & Voting
- Stance range: **0–100**
- Interpretation: `>50` = guilty, `<=50` = not guilty
- Stance updates from:
  - topic weights parsed from `<!-- ANALYSIS -->` tags
  - weakness keyword triggers (moves stance toward neutral)
- Final vote is cast **by jurors via tools** in `/vote` (not a server-side calculation)

### ReAct Agent Loop
- Jurors use **spoon-core ToolCallAgent** with tools:
  - `lookup_evidence` (self-initiated evidence lookup)
  - `cast_vote` (on-chain voting)
- Tool results are written into memory as `tool` messages so the agent can reference them later.
- When uncertain, jurors are instructed to call `lookup_evidence`.

### Evidence System
- Evidence stored in `content/case/evidence/*.json`.
- Evidence IDs can be:
  - internal IDs (e.g., `E1`, `E10`)
  - file stems (e.g., `log_injection`)
  - legacy IDs (`chat_history`, `safety_report`, `dossier`)
- Locked evidence is enforced via session state.

### Persuasion Phase Rules
- Each juror has **10 total rounds** per session.
- **Chat messages and evidence presentation both consume a round**.
- UI shows remaining rounds and disables input at 0.

### Voting
- `/vote` triggers each juror to decide and call `cast_vote`.
- Requires contract address + private keys (`JURY_VOTING_PRIVATE_KEYS`).

### Flow Diagram (Simplified)
```
Prologue (story/opening)
  ↓
Investigation (dossier/evidence/witness)
  ↓  setPhase(investigation, session_id)
Persuasion (juror chat + present evidence)
  ↓  setPhase(persuasion, session_id)
Verdict (juror tool voting)
  ↓  setPhase(verdict, session_id)
On-chain result + ending
```

## API Quick Reference

**Session-bound endpoints (must include `session_id`):**
- `POST /phase/{phase}?session_id=...`
- `GET /story/blake?session_id=...`
- `POST /witness/{id}/chat?session_id=...`
- `POST /witness/{id}/present/{evidence_id}?session_id=...`
- `GET /content/evidence?session_id=...`
- `GET /content/evidence/{id}?session_id=...`
- `POST /chat/{juror_id}?session_id=...`
- `POST /juror/{id}/present/{evidence_id}?session_id=...`

**Session / Phase**
- `GET /state`
- `POST /phase/{phase}?session_id=...`  (syncs session phase)
  - Response: `{ "phase": "investigation|persuasion|verdict|prologue" }`

**Prologue**
- `GET /story/opening`
  - Response: `{ session_id, text }`
- `GET /story/blake?session_id=...`
  - Response: `{ round, text, options: [{ id, text }] }`
- `POST /story/blake/respond`
  - Body: `{ session_id, option_id }`
  - Response: `{ response_text, next_round, phase }`

**Investigation**
- `GET /content/dossier`
- `GET /content/dossier`
  - Response: `{ title, summary, sections[] }`
- `GET /content/evidence?session_id=...`
- `GET /content/evidence?session_id=...`
  - Response: `[{ id, name, icon, internal_id, locked }]`
- `GET /content/evidence/{id}?session_id=...`
- `GET /content/evidence/{id}?session_id=...`
  - Response: `{ id, name, description, content, locked? }`
- `GET /content/witnesses`
- `GET /content/witnesses`
  - Response: `[{ id, name, portrait }]`
- `GET /content/witness/{id}`
- `POST /witness/{id}/chat?session_id=...`
- `POST /witness/{id}/chat?session_id=...`
  - Body: `{ message? , option_id? }`
  - Response: `{ text, options[], is_llm, node_id? }`
- `POST /witness/{id}/present/{evidence_id}?session_id=...`
- `POST /witness/{id}/present/{evidence_id}?session_id=...`
  - Response: `{ text, unlocks[], forced }`

**Persuasion**
- `GET /jurors`
  - Response: `[{ id, name, stance_label, first_message }]`
- `GET /juror/{id}`
  - Response: `{ id, name, first_message }`
- `POST /chat/{juror_id}?session_id=...`
  - Body: `{ message }`
  - Response: `{ reply, juror_id, rounds_left, weakness_triggered, tool_actions[], has_voted }`
- `POST /juror/{id}/present/{evidence_id}?session_id=...`
  - Response: `{ text, stance_delta, rounds_left, weakness_triggered }`

**Verdict**
- `POST /vote`
  - Response: `{ guilty_votes, not_guilty_votes, verdict, tx_hashes, votes[] }`
- `GET /story/ending?verdict=...`
  - Response: `{ type, title, text, blake_reaction }`

## Troubleshooting

See `TROUBLESHOOTING.md` for voting stalls, spoon-core import errors, and port conflicts.

---

## Changelog

### v0.3.0 - Juror System Overhaul (2026-01-31)

Expanded the persuasion phase with new juror configs, stance model, round limits, and evidence presentation.

**New Gameplay Features:**
- **5 jurors** with updated personalities
- **Stance scale switched to 0–100** with vote threshold at `> 50` guilty
- **Per-juror dialogue limit** (10 rounds) with UI countdown
- **Present evidence to juror** (`POST /juror/{id}/present/{evidence_id}`) consumes a round
- **Weakness trigger detection** with visual feedback

**Prompt System:**
- Juror system prompts now composed from `content/prompts/common_prefix.md` + juror `role_prompt` + `content/prompts/juror_suffix.md`
- Evidence index injected so jurors can self‑initiate tool calls

**Backend Changes:**
- `backend/agents/spoon_juror_agent.py` - new `JurorConfig` fields (role_prompt/weakness), weakness detection, 0–100 stance clamp, tool-call fixes
- `backend/main.py` - session‑scoped round limits, juror evidence endpoint, phase sync support via `session_id`
- `backend/services/agent_manager.py` - new JSON format support, juror metadata for frontend
- `backend/tools/evidence_tool.py` - supports internal IDs (E1–E10) and multi‑lookup via `evidence_ids`
- `backend/tools/spoon_voting_tool.py` - non‑blocking vote execution

**Frontend Changes:**
- `frontend/js/game.js` - juror cards w/ stance hint, rounds badge, weakness flash, juror evidence flow, session_id wiring
- `frontend/js/api.js` - session_id added to juror APIs
- `frontend/index.html` - rounds counter + evidence button in chat header
- `frontend/css/style.css` - rounds badge + weakness animation + evidence “shown” state

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
