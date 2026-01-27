# Codex Execution Guide

Use this guide to run or validate the current AI Trial implementation.

## Principles

1. Execute steps in order.
2. Test after each major change.
3. Fix failures before proceeding.
4. Keep changes minimal and focused.

## Phase 1: Contracts

1. Build and test
   ```bash
   cd ai-trial-game/contracts
   forge build
   forge test -vv
   ```
2. Local deployment (optional)
   ```bash
   anvil
   forge script script/Deploy.s.sol --broadcast --rpc-url http://127.0.0.1:8545
   ```
3. Record deployed contract address for backend configuration.

## Phase 2: Backend

1. Install dependencies
   ```bash
   cd ai-trial-game/backend
   pip install -r requirements.txt
   ```
2. Verify imports
   ```bash
   py -c "from services.agent_manager import AgentManager; print('OK')"
   ```
3. Start API server
   ```bash
   py -m uvicorn main:app --reload --port 8001
   ```

## Phase 3: SpoonOS Juror Agents (ReAct)

- Juror agents are implemented in `backend/agents/spoon_juror_agent.py`.
- AgentManager loads jurors from `content/jurors/`.
- LLM settings are read from `.env`:
  - `OPENAI_COMPATIBLE_API_KEY`
  - `OPENAI_COMPATIBLE_BASE_URL`
  - `OPENAI_COMPATIBLE_MODEL`

Quick import check:
```bash
py -c "from agents.spoon_juror_agent import SpoonJurorAgent; print('OK')"
```

## Phase 4: API Verification

Basic endpoints:
```bash
curl http://localhost:8001/
curl http://localhost:8001/state
curl http://localhost:8001/jurors
```

Chat endpoint (requires persuasion phase and API key):
```bash
curl -X POST http://localhost:8001/phase/persuasion
curl -X POST http://localhost:8001/chat/juror_wang \
  -H "Content-Type: application/json" \
  -d '{"message":"Test"}'
```

## Phase 5: Frontend

1. Open `ai-trial-game/frontend/index.html` in a browser.
2. Ensure it calls the backend API at the correct host/port.
3. Walk through investigation -> persuasion -> verdict.

## Common Issues

- Base URL should end at `/v1`, not `/chat/completions`.
- Ensure API keys are set in `.env` under `ai-trial-game/backend`.
- If a port is in use, change `SERVER_PORT` in `.env`.
