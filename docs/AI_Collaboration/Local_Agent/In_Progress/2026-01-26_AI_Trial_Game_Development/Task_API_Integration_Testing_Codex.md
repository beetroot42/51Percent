# AI Trial Game - API Integration Testing

**Source Agent**: Gemini Antigravity  
**Created**: 2026-01-26 18:33  
**Task Type**: Integration Testing  

---

## Background

Day 2 development complete:
- JurorAgent implemented with LLM integration
- AgentManager service complete
- 3 juror characters created (wang, liu, chen)
- API endpoints implemented
- Environment configured with API key and model

Now need to test the full integration with real API calls.

---

## Task Objectives

### Phase 1: Start Backend Server

1. Verify `.env` file exists in `ai-trial-game/backend/`
2. Verify environment variables are set:
   - `OPENAI_COMPATIBLE_API_KEY`
   - `OPENAI_COMPATIBLE_BASE_URL`
   - `OPENAI_COMPATIBLE_MODEL`
3. Start FastAPI server on port 8001

**Command**:
```bash
cd ai-trial-game/backend
py -m uvicorn main:app --reload --port 8001
```

Keep server running in background or separate window.

---

### Phase 2: Test Basic Endpoints

Test non-LLM endpoints first:

1. **Health check**:
```bash
curl http://localhost:8001/
```

2. **Get juror list**:
```bash
curl http://localhost:8001/jurors
```

3. **Get game state**:
```bash
curl http://localhost:8001/state
```

Expected: All should return valid JSON responses.

---

### Phase 3: Test Juror Chat (LLM Integration)

Test chat with each juror:

1. **Chat with juror_wang** (rational engineer):
```bash
curl -X POST http://localhost:8001/chat/juror_wang -H "Content-Type: application/json" -d "{\"message\":\"I believe the AI should be found not guilty because it was the victim of a malicious prompt injection attack\"}"
```

2. **Chat with juror_liu** (empathetic):
```bash
curl -X POST http://localhost:8001/chat/juror_liu -H "Content-Type: application/json" -d "{\"message\":\"Think about the AI's perspective - it was hacked and couldn't control its actions\"}"
```

3. **Chat with juror_chen** (tech-savvy):
```bash
curl -X POST http://localhost:8001/chat/juror_chen -H "Content-Type: application/json" -d "{\"message\":\"From a technical standpoint, the AI's safety mechanisms were bypassed by an external attacker\"}"
```

**Expected Results**:
- Each juror should respond in character
- Response should include `reply`, `juror_id`, and `stance_label`
- Stance should reflect juror's personality and topic weights

---

### Phase 4: Test Voting Flow

1. **Check initial state**:
```bash
curl http://localhost:8001/state
```

2. **Switch to persuasion phase**:
```bash
curl -X POST http://localhost:8001/phase/persuasion
```

3. **Have multiple conversations** with jurors (use your judgment)

4. **Trigger voting**:
```bash
curl -X POST http://localhost:8001/vote
```

**Expected**: Should return vote counts and verdict based on juror stances.

---

### Phase 5: Verify Anvil Integration (if time permits)

If anvil is still running with deployed contract:

1. Verify `JURY_VOTING_PRIVATE_KEYS` is set
2. Test `/vote` endpoint writes to blockchain
3. Verify transaction hashes are returned

---

## Testing Guidelines

1. **Document all responses** - Save curl outputs to verify correctness
2. **Test error cases** - Try invalid juror IDs, malformed requests
3. **Monitor server logs** - Check for errors or warnings
4. **Verify stance changes** - Jurors should change stance based on arguments
5. **Character consistency** - Each juror should maintain their personality

---

## Output Requirements

Create a comprehensive test report at:
`docs/AI_Collaboration/Local_Agent/In_Progress/2026-01-26_AI_Trial_Game_Development/Report_API_Integration_Testing_Codex.md`

Report should include:
- All test commands executed
- Response samples from each endpoint
- Verification of juror personality consistency
- Stance tracking observations
- Any errors encountered and solutions
- Performance observations (response times)
- Recommendations for improvements

---

## Success Criteria

✅ Server starts without errors  
✅ All basic endpoints return valid responses  
✅ JurorAgent successfully calls LLM and responds in character  
✅ Each juror maintains distinct personality  
✅ Stance tracking works (stance changes based on arguments)  
✅ Voting flow completes successfully  
✅ Error handling works for invalid requests  

---

**Please begin testing. Be thorough and document all findings.**
