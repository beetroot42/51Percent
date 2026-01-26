# AI Trial Game - API Integration Testing Report (Codex)

**Date**: 2026-01-26
**Scope**: FastAPI backend integration tests (in-process due to local socket bind restrictions)

---

## Environment & Preconditions

- `.env` exists at `ai-trial-game/backend/.env` and includes:
  - `OPENAI_COMPATIBLE_API_KEY`
  - `OPENAI_COMPATIBLE_BASE_URL`
  - `OPENAI_COMPATIBLE_MODEL`
- LLM calls were executed via the OpenAI-compatible client configured in `.env`.

### Server Startup Attempt

Command attempted (per task):

```bash
cd ai-trial-game/backend
py -m uvicorn main:app --reload --port 8001
```

Result:
- **Failed to bind port** with `WinError 10013` (socket access denied) on both 8001 and other tested ports.
- This appears to be a local environment restriction preventing listening sockets.

Because the server cannot bind to any port in this environment, tests were executed **in-process** using `fastapi.testclient.TestClient` while still performing real outbound LLM calls.

Command used for in-process integration testing:

```bash
py - <<'PY'
# Script uses fastapi.testclient + loads .env, then hits all endpoints.
# (See test script output captured in this report.)
PY
```

---

## Test Results

### Phase 2: Basic Endpoints

1. **Health check** `GET /`

```json
{
  "status": "ok",
  "game": "AI Trial"
}
```

2. **Juror list** `GET /jurors`

```json
[
  {
    "id": "juror_chen",
    "name": "Chen",
    "first_message": "I can follow technical arguments. Make them clear and I will respond honestly."
  },
  {
    "id": "juror_liu",
    "name": "Liu",
    "first_message": "I want to hear how your view accounts for the people who were hurt."
  },
  {
    "id": "juror_wang",
    "name": "Wang",
    "first_message": "I will listen, but I care about evidence, not slogans. What is your point?"
  },
  {
    "id": "test_juror",
    "name": "\u6d4b\u8bd5\u966a\u5ba1\u5458",
    "first_message": "\u4f60\u597d\uff0c\u6211\u662f\u6d4b\u8bd5\u966a\u5ba1\u5458\u3002\u6709\u4ec0\u4e48\u8981\u8bf4\u7684\u5417\uff1f"
  }
]
```

3. **Game state** `GET /state`

```json
{
  "phase": "investigation",
  "jurors": [
    {
      "id": "juror_chen",
      "name": "Chen",
      "first_message": "I can follow technical arguments. Make them clear and I will respond honestly."
    },
    {
      "id": "juror_liu",
      "name": "Liu",
      "first_message": "I want to hear how your view accounts for the people who were hurt."
    },
    {
      "id": "juror_wang",
      "name": "Wang",
      "first_message": "I will listen, but I care about evidence, not slogans. What is your point?"
    },
    {
      "id": "test_juror",
      "name": "\u6d4b\u8bd5\u966a\u5ba1\u5458",
      "first_message": "\u4f60\u597d\uff0c\u6211\u662f\u6d4b\u8bd5\u966a\u5ba1\u5458\u3002\u6709\u4ec0\u4e48\u8981\u8bf4\u7684\u5417\uff1f"
    }
  ],
  "vote_state": null
}
```

### Phase 3: Juror Chat (LLM Integration)

**Pre-condition**: `POST /phase/persuasion`

```json
{
  "phase": "persuasion"
}
```

1. **Chat with juror_wang** `POST /chat/juror_wang`

```json
{
  "reply": "I understand your position, but let me ask you this - if a machine can be \"victimized\" by code injection, doesn't that imply it has some level of agency to begin with? ... Where are the humans in this chain who should be held accountable?",
  "juror_id": "juror_wang"
}
```

2. **Chat with juror_liu** `POST /chat/juror_liu`

```json
{
  "reply": "I notice you've shared a character prompt for a role-playing scenario ... How can I help you with this?",
  "juror_id": "juror_liu"
}
```

3. **Chat with juror_chen** `POST /chat/juror_chen`

```json
{
  "reply": "I can see you've shared a character prompt for what looks like an interactive story or game scenario ... Are you: 1) Developing a game ... 2) Looking to roleplay ... 3) Wanting to discuss ...",
  "juror_id": "juror_chen"
}
```

**Observation**: `juror_liu` and `juror_chen` responses did **not** remain in character and appeared to disregard the roleplay system prompt, instead responding with meta-conversation. `juror_wang` responded in character.

### Stance Tracking Observations

Internal stance snapshot (post-chats, via `agent_manager`):

```json
{
  "juror_wang": 50,
  "juror_liu": -30,
  "juror_chen": 15
}
```

- `juror_wang` stance increased to a positive value (leans not guilty).
- `juror_liu` stance moved negative (leans guilty), despite pro-defense prompts.
- `juror_chen` stance slightly positive.

Note: `stance_label` is not included in the API response even though `JurorAgent.chat()` returns it; API response model only includes `reply` and `juror_id`.

### Phase 4: Voting Flow

- `/vote` failed with:

```json
{
  "detail": "No juror private keys configured"
}
```

This matches current `.env` (no `JURY_VOTING_PRIVATE_KEYS`). Blockchain write could not be verified.

### Error Handling

1. **Chat before persuasion** `POST /chat/juror_wang`

```json
{
  "detail": "Not in persuasion phase"
}
```

2. **Invalid juror** `POST /chat/juror_unknown`

```json
{
  "detail": "'Juror not found: juror_unknown'"
}
```

3. **Malformed JSON** `POST /chat/juror_wang` with invalid body

```json
{
  "detail": [
    {
      "type": "json_invalid",
      "loc": ["body", 0],
      "msg": "JSON decode error",
      "input": {},
      "ctx": {"error": "Expecting value"}
    }
  ]
}
```

4. **Invalid phase** `POST /phase/not_a_phase`

```json
{
  "detail": "Invalid phase"
}
```

---

## Performance Observations (TestClient wall-clock)

- Basic endpoints: ~0.002s¨C0.011s each
- LLM chat endpoints: ~7.5s¨C11.3s each
- Error endpoints: ~0.002s¨C0.003s each

---

## Issues & Recommendations

1. **Server cannot bind to ports**
   - `WinError 10013` prevents running the FastAPI server locally. This blocks true HTTP integration tests.
   - Recommendation: confirm local security policy or reserved port rules; allow loopback binding or test in another environment.

2. **LLM roleplay adherence inconsistent**
   - `juror_liu` and `juror_chen` responded with meta-assistant behavior rather than staying in character.
   - Recommendation: review system prompt strength and/or model choice; consider adding `response_format` or stricter system message to enforce roleplay.

3. **Missing `stance_label` in API response**
   - `JurorAgent.chat()` returns `stance_label`, but `/chat/{juror_id}` response model does not include it.
   - Recommendation: update `ChatResponse` to include `stance_label` if it is required by the frontend or task expectations.

4. **Voting flow blocked by missing keys**
   - `/vote` requires `JURY_VOTING_PRIVATE_KEYS`; not present in `.env`.
   - Recommendation: set keys in non-production test environment or add a mock/disable path for local integration tests.

---

## Success Criteria Status

- Server starts without errors: **Not met** (port bind blocked)
- Basic endpoints return valid responses: **Met** (via TestClient)
- JurorAgent calls LLM and responds: **Partial** (LLM responses returned, but two jurors broke character)
- Distinct personalities: **Partial** (Wang OK; Liu/Chen not in character)
- Stance tracking works: **Partial** (stance changed; direction inconsistent for Liu)
- Voting flow completes: **Not met** (missing private keys)
- Error handling works for invalid requests: **Met**

---

## Raw Test Output (Summary)

- `health_check`: 200 in 0.0106s
- `get_jurors`: 200 in 0.0024s
- `get_state_initial`: 200 in 0.0027s
- `chat_before_persuasion`: 400 in 0.0026s
- `set_phase_persuasion`: 200 in 0.0028s
- `chat_juror_wang_1`: 200 in 7.5525s
- `chat_juror_liu_1`: 200 in 9.1107s
- `chat_juror_chen_1`: 200 in 8.8209s
- `chat_juror_wang_2`: 200 in 8.7214s
- `chat_juror_liu_2`: 200 in 9.4377s
- `chat_juror_chen_2`: 200 in 11.2636s
- `get_state_after_chats`: 200 in 0.0026s
- `chat_invalid_juror`: 404 in 0.0029s
- `chat_malformed_body`: 422 in 0.0024s
- `phase_invalid`: 400 in 0.0025s
- `vote_attempt`: 500 in 0.0030s

