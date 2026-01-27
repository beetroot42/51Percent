# AI Trial - System Architecture

> Blockchain jury persuasion game built on SpoonOS ReAct agents.

## Implementation Status

| Component | Status | Description |
| --- | --- | --- |
| SpoonJurorAgent | Implemented | SpoonOS ReAct-based juror agent in `backend/agents/spoon_juror_agent.py` |
| AgentManager | Implemented | Orchestrates juror agents in `backend/services/agent_manager.py` |
| VotingTool | Implemented | On-chain voting tool in `backend/tools/voting_tool.py` |
| Integration Tests | Added | `backend/tests/test_spoon_integration.py` |

## I. Game Background

In a future court system, juries are selected via blockchain to ensure fairness and transparency.

**Case**: A prompt-injection-induced embodied AI homicide case
- Core conflict: Is the AI the perpetrator or the victim?
- Player role: Detective (neutral investigator)
- Objective: Investigate the case, then persuade jurors

## II. Game Flow (High Level)

1. Investigation phase
   - Read dossier
   - Review evidence
   - Interview witnesses
2. Persuasion phase
   - Chat with jurors (SpoonOS ReAct agents)
   - Influence hidden stances through arguments
3. Verdict phase
   - Collect juror votes
   - On-chain vote execution
   - Display final verdict

## III. System Architecture

Frontend (HTML/CSS/JS)
  -> Game API (FastAPI)
     -> SpoonOS Core (ReAct juror agents + tools)
        -> Blockchain (Foundry contract)

### Frontend
- Investigation UI: dossier, evidence, witnesses
- Persuasion UI: juror list and chat
- Verdict UI: voting animation and results

### Game API (FastAPI)
- `GET /` health check
- `GET /state` game phase and juror info
- `POST /phase/{phase_name}` switch game phase
- `GET /jurors` list jurors
- `GET /juror/{juror_id}` juror info
- `POST /chat/{juror_id}` chat with juror
- `POST /vote` trigger voting
- `POST /reset` reset game
- `GET /content/*` dossier/evidence/witness content

### SpoonOS Core (ReAct Agents)
- Each juror is a SpoonOS ReAct agent
- Juror stance is hidden and updated per dialogue
- Topic analysis is embedded in agent replies and parsed server-side

### Blockchain (Foundry)
- `JuryVoting.sol` counts votes and determines verdict

## IV. Content Layer

```
content/
  case/
    dossier.json
    evidence/
      *.json
  witnesses/
    *.json
  jurors/
    *.json
```

## V. Smart Contract Summary

- Tracks per-address votes
- Prevents double voting
- Closes voting when all jurors have voted
- Returns final verdict based on majority

## VI. Repository Layout

```
ai-trial-game/
  contracts/
  backend/
  frontend/
  content/
  README.md
```
