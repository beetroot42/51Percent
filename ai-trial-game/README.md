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
