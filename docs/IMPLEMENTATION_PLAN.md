# AI Trial - Implementation Plan

> 5-day Hackathon: 3 days coding + 2 days content

## Time Allocation

```
Day 1 ████████████████████ Code: Contracts + Backend skeleton
Day 2 ████████████████████ Code: Agent + Complete API
Day 3 ████████████████████ Code: Frontend + Integration
Day 4 ████████████████████ Content: Evidence/Witnesses/Jurors
Day 5 ████████████████████ Content: Polish + Demo prep
```

---

## Day 1: Contracts + Backend Skeleton

### Morning: Foundry Contracts

| Task | Output |
|------|---------|
| Initialize Foundry project | `contracts/` directory |
| Write JuryVoting contract | `JuryVoting.sol` |
| Write tests | Basic voting logic tests pass |
| Local deployment | anvil running + contract deployed |

```bash
# Acceptance commands
cd contracts && forge test
anvil &
forge script script/Deploy.s.sol --broadcast --rpc-url http://127.0.0.1:8545
```

### Afternoon: Backend Skeleton

| Task | Output |
|------|---------|
| Initialize Python project | FastAPI + requirements.txt |
| Set up spoon-core environment | Can import spoon_ai |
| Write VotingTool | Tool to call contract |
| Basic API | `/state` endpoint returns data |

```bash
# Acceptance commands
cd backend && pip install -r requirements.txt
python -c "from spoon_ai import SpoonReactAI; print('OK')"
uvicorn main:app --reload
curl http://localhost:8000/state
```

### Day 1 Deliverables

```
contracts/
├── src/JuryVoting.sol       ✓
├── test/JuryVoting.t.sol    ✓
└── script/Deploy.s.sol      ✓

backend/
├── main.py                  ✓ (Basic FastAPI)
├── tools/voting_tool.py     ✓
└── requirements.txt         ✓
```

---

## Day 2: Agent + Complete API

### Morning: Juror Agent

| Task | Output |
|------|---------|
| Write JurorAgent class | Inherit from SpoonReactAI |
| Character card loading logic | Read JSON to generate prompt |
| Conversation history management | Use spoon-core Memory |
| Stance tracking | Return current stance after dialogue |

```python
# Acceptance: Can dialogue with a test juror
agent = JurorAgent("juror_a")
response = await agent.chat("I think the AI is innocent")
print(response.reply, response.stance)
```

### Afternoon: Complete API

| Task | Output |
|------|---------|
| `/chat/{juror_id}` | Chat with juror |
| `/vote` | Trigger voting |
| `/state` | Complete game state |
| Multi-Agent management | AgentManager class |

```bash
# Acceptance commands
curl -X POST http://localhost:8000/chat/juror_a \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'

curl -X POST http://localhost:8000/vote
```

### Day 2 Deliverables

```
backend/
├── agents/
│   └── juror_agent.py       ✓
├── services/
│   └── agent_manager.py     ✓
└── main.py                  ✓ (Complete API)

content/
└── jurors/
    └── _template.json       ✓ (Character card template)
```

---

## Day 3: Frontend + Integration

### Morning: Frontend UI

| Task | Output |
|------|---------|
| HTML skeleton | Three phase pages |
| Investigation phase UI | Dossier/evidence/witnesses |
| Persuasion phase UI | Juror list + dialogue box |
| Trial phase UI | Voting result display |

### Afternoon: Integration

| Task | Output |
|------|---------|
| Frontend calls backend API | Fetch logic |
| Dialogue tree engine | Witness dialogue + present evidence |
| Voting flow | Trigger vote → display results |
| End-to-end testing | Complete flow works |

### Day 3 Deliverables

```
frontend/
├── index.html               ✓
├── css/style.css            ✓
├── js/
│   ├── game.js              ✓ (Game main logic)
│   ├── dialogue.js          ✓ (Dialogue tree engine)
│   └── api.js               ✓ (API calls)
└── assets/                  (placeholder images)
```

### Day 3 Acceptance

```
Complete flow:
1. Open page → See investigation phase
2. Read dossier → View evidence → Dialogue with witnesses
3. Click "Enter persuasion" → Free dialogue with jurors
4. Click "Start trial" → See voting results → Display ending
```

---

## Day 4-5: Content Creation

### Day 4: Core Content

| Task | Quantity |
|------|----------|
| Dossier text | 1 file |
| Evidence | 3-5 items |
| Witnesses | 2-3 people |
| Witness dialogue tree | 10+ nodes per person |
| Evidence reactions | Each evidence × each witness |
| Juror character cards | 3-5 people |

### Day 5: Polish + Demo

| Task | Description |
|------|-------------|
| Content testing | Play through several times |
| Bug fixes | Fix integration issues |
| Asset supplement | Pixel art/icons |
| Demo script | Prepare demonstration flow |
| Deployment | GitHub Pages / Vercel |

---

## Dependencies

```
Day 1 Contracts ────┐
                   ├──▶ Day 2 Agent+API ──▶ Day 3 Frontend integration
Day 1 Backend skeleton──┘                              │
                                                       ▼
                            Day 4-5 Content creation (can start in parallel with Day 3)
```

---

## Risk Points

| Risk | Response |
|------|----------|
| Unfamiliar with spoon-core API | Reference examples/, ask documentation |
| LLM API rate limiting | Use cheaper model, add caching |
| Frontend struggles | Use simplest HTML, don't pursue aesthetics |
| Can't finish content | Ensure 2 witnesses + 3 jurors playable first |

---

## Minimum Playable Version (If Time Runs Out)

By end of Day 3 must have:
- Display 1 dossier
- Choice dialogue with 1 witness
- Agent dialogue with 1 juror
- Trigger voting to see results

That's enough for demo, everything else is polish.

---

## MVP Content Quantity

| Content | Quantity |
|---------|----------|
| Dossier | 1 file |
| Evidence | 3-5 items |
| Witnesses | 3 people |
| Jurors | 3 people |
