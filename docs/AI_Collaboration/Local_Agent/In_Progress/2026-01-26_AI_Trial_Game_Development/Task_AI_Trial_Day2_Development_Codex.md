# AI Trial Game - Day 2 Development Tasks

**Source Agent**: Gemini Antigravity  
**Created**: 2026-01-26 17:26  
**Task Type**: Code Generation/Implementation  

---

## Background

This is a 5-day hackathon project "AI Trial", a blockchain jury persuasion game. Day 1 is complete:
- JuryVoting contract implemented and tested (10/10 tests pass)
- Contract deployed to local anvil at `0x5FbDB2315678afecb367f032d93F642f64180aa3`
- VotingTool backend integration tested (5/5 tests pass)
- FastAPI skeleton created with basic endpoints

Now Day 2 focuses on implementing the AI jury persuasion system.

---

## Development Guidelines

1. **Use English**: All code comments and variable names in English to avoid encoding issues
2. **Reference Design Doc**: Follow `docs/AGENT_DESIGN.md` for detailed specifications
3. **SpoonOS Pitfalls**: Reference `docs/spoonOS_development_pitfalls.md` for configuration best practices
4. **Test-Driven**: Every implementation must be tested before moving to next task

---

## Task Objectives

### Phase 1: Complete JurorAgent Implementation

**File**: `ai-trial-game/backend/agents/juror_agent.py`

The file has a partial implementation. Complete all TODO methods:

1. **Verify existing implementation** - A previous implementation exists, test if it works
2. **Fix any issues** - Ensure LLM client initialization works with OpenAI-compatible API
3. **Test the agent** - Create a simple test to verify the agent can load config and respond

**Acceptance Test**:
```python
# In backend directory
import asyncio
from agents.juror_agent import JurorAgent

async def test():
    agent = JurorAgent("test_juror", content_path="../content/jurors")
    response = await agent.chat("I believe the AI should be found not guilty")
    print(response)

asyncio.run(test())
```

---

### Phase 2: Complete AgentManager Implementation

**File**: `ai-trial-game/backend/services/agent_manager.py`

Implement all TODO methods:
1. `load_all_jurors()` - Scan directory and create JurorAgent instances
2. `get_juror()` - Return agent by ID
3. `chat_with_juror()` - Delegate to agent.chat()
4. `get_all_juror_info()` - Return basic info for frontend
5. `collect_votes()` - Get final votes from all jurors
6. `reset_all()` - Reset all agents

---

### Phase 3: Complete API Endpoints

**File**: `ai-trial-game/backend/main.py`

Implement the following endpoints:

1. **`POST /chat/{juror_id}`** - Chat with a juror
   - Check if game phase is "persuasion"
   - Call agent_manager.chat_with_juror()
   - Return reply

2. **`POST /vote`** - Trigger voting
   - Collect votes from agent_manager
   - Call voting_tool.cast_all_votes()
   - Return verdict

3. **`GET /jurors`** - List all jurors
   - Return basic info

4. **`POST /phase/{phase_name}`** - Switch game phase
   - Validate phase name
   - Update global game_phase

---

### Phase 4: Create Test Juror Characters

**Directory**: `ai-trial-game/content/jurors/`

Create 3 juror character cards following the template:
1. `juror_wang.json` - Rational engineer type, values technical evidence
2. `juror_liu.json` - Empathetic type, sympathizes with victims
3. `juror_chen.json` - Tech-savvy programmer, understands AI

Follow the format in `_template.json` and refer to examples in `docs/AGENT_DESIGN.md`.

---

## Related Files

| File | Path | Description |
|------|------|-------------|
| JurorAgent | `ai-trial-game/backend/agents/juror_agent.py` | Needs verification/fixes |
| AgentManager | `ai-trial-game/backend/services/agent_manager.py` | TODOs to implement |
| Main API | `ai-trial-game/backend/main.py` | Add endpoint implementations |
| Agent Design | `docs/AGENT_DESIGN.md` | Detailed specifications |
| Pitfalls | `docs/spoonOS_development_pitfalls.md` | Configuration best practices |
| Juror Template | `ai-trial-game/content/jurors/_template.json` | Character card format |

---

## Verification Commands

```bash
# Test JurorAgent (requires API key configured)
cd ai-trial-game/backend
py -c "from agents.juror_agent import JurorAgent; print('Import OK')"

# Test AgentManager
py -c "from services.agent_manager import AgentManager; print('Import OK')"

# Start FastAPI server
py -m uvicorn main:app --reload --port 8001

# Test endpoints
curl http://localhost:8001/state
curl http://localhost:8001/jurors
curl -X POST http://localhost:8001/chat/juror_wang -H "Content-Type: application/json" -d "{\"message\":\"Test\"}"
```

---

## Output Requirements

1. Directly modify the files listed above
2. Ensure all imports work without errors
3. Save completion report to: `docs/AI_Collaboration/Local_Agent/In_Progress/2026-01-26_AI_Trial_Game_Development/Report_AI_Trial_Day2_Development_Codex.md`

Report should include:
- List of completed tasks
- Any issues encountered and solutions
- Test results
- Next steps recommendations

---

**Please begin execution. Analyze the existing code structure, complete tasks in sequence. Report any problems encountered.**
