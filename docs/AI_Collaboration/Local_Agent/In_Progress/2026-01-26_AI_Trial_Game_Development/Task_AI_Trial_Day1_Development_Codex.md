# AI Trial Game - Day 1 Development Tasks

**Source Agent**: Gemini Antigravity  
**Created**: 2026-01-26 16:08  
**Task Type**: Code Generation/Implementation  

---

## Background

This is a 5-day hackathon project "AI Trial", a blockchain jury persuasion game based on SpoonOS. Currently in Day 1 phase, need to complete:
1. Smart contract implementation
2. Backend basic framework

Project skeleton exists at `d:\51-DEMO\ai-trial-game\`, but core code are all TODO placeholders that need implementation.

---

## ⚠️ Development Precautions (Must Read)

Refer to lessons learned in `docs/spoonOS_development_pitfalls.md`:

1. **Virtual Environment**: If running Python, ensure using correct virtual environment
2. **OpenAI Compatible Provider**: If using spoon-core, note Provider needs explicit registration
3. **Base URL Configuration**: Only configure to `/v1`, don't include `/chat/completions`
4. **Test-Driven**: Every step must pass testing after implementation

---

## Task Objectives

Following the sequence in `docs/CODEX_EXECUTION_GUIDE.md`, complete the following tasks:

### Phase 1: Smart Contracts (Task 1.1 - 1.3)

**Working Directory**: `d:\51-DEMO\ai-trial-game\contracts`

1. **Task 1.1**: Implement constructor in `src/JuryVoting.sol`
   - Validate `_totalJurors > 0`
   - Set `totalJurors`

2. **Task 1.2**: Implement `vote` function
   - Check if already voted
   - Check if voting has ended
   - Record voting status
   - Update vote count
   - Check if voting should close
   - Trigger `Voted` event

3. **Task 1.3**: Implement `getVoteState` and `getVerdict` functions
   - `getVoteState`: Return current voting state
   - `getVerdict`: Return final verdict (need to check voting has ended)
   - Implement `closeVoting` forced end functionality

4. Create test file `test/JuryVoting.t.sol`, refer to test code in CODEX_EXECUTION_GUIDE.md

**Verification Commands**:
```bash
cd d:\51-DEMO\ai-trial-game\contracts
forge build
forge test -vv
```

**Acceptance Criteria**: All tests pass

---

### Phase 2: Backend Basics (Task 2.1 - 2.3)

**Working Directory**: `d:\51-DEMO\ai-trial-game\backend`

1. **Task 2.1**: Implement `_init_web3` method in `tools/voting_tool.py`
   - Use web3.py to connect
   - Define contract ABI
   - Create contract instance

2. **Task 2.2**: Implement complete `VotingTool` functionality
   - `get_vote_state()`: Query voting status
   - `cast_vote()`: Execute voting
   - `get_verdict()`: Get verdict result

3. **Task 2.3**: Implement basic endpoints in `main.py`
   - Implement `get_game_state` to return mock data
   - Ensure `/` and `/state` endpoints work

---

## Related Files

| File | Path | Description |
|------|------|-------------|
| Contract | `ai-trial-game/contracts/src/JuryVoting.sol` | Need to implement TODO |
| Contract Tests | `ai-trial-game/contracts/test/JuryVoting.t.sol` | Need to create/implement |
| Deploy Script | `ai-trial-game/contracts/script/Deploy.s.sol` | Check if complete |
| Voting Tool | `ai-trial-game/backend/tools/voting_tool.py` | Need to implement TODO |
| API Main Entry | `ai-trial-game/backend/main.py` | Need to implement TODO |
| Execution Guide | `docs/CODEX_EXECUTION_GUIDE.md` | Detailed implementation reference |
| Architecture Design | `docs/ARCHITECTURE.md` | System architecture reference |
| Pitfalls Log | `docs/spoonOS_development_pitfalls.md` | Development precautions |

---

## Output Requirements

1. Directly modify above files, implement all TODOs
2. Ensure verification commands for each phase can pass
3. Save completion report to: `docs/AI_Collaboration/Local_Agent/In_Progress/2026-01-26_AI_Trial_Game_Development/Report_AI_Trial_Day1_Development_Codex.md`

Report should include:
- List of completed tasks
- Problems encountered and solutions
- Verification result screenshots/outputs
- Next step recommendations

---

**Please begin execution. Autonomously analyze code structure, complete tasks in sequence. Record any problems encountered in the report.**
