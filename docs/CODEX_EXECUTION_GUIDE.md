# Codex Execution Plan

> Execute in sequence, each step must pass testing before proceeding to the next

## Execution Principles

1. **Strict sequential execution** - Don't skip steps
2. **Test every step** - Only continue after tests pass
3. **Fix issues first** - Don't continue with bugs
4. **Keep code simple** - Don't over-engineer

---

## Phase 1: Smart Contracts (Day 1 Morning)

### Task 1.1: Implement JuryVoting Constructor

**File**: `contracts/src/JuryVoting.sol`

**Implementation Requirements**:
```solidity
constructor(uint _totalJurors) {
    require(_totalJurors > 0, "Must have at least 1 juror");
    totalJurors = _totalJurors;
}
```

**Testing Method**:
```bash
cd ai-trial-game/contracts
forge build
```

**Acceptance Criteria**: Compiles successfully, no errors

---

### Task 1.2: Implement vote Function

**File**: `contracts/src/JuryVoting.sol`

**Implementation Requirements**:
- Check if already voted
- Check if voting has closed
- Record vote
- Update vote count
- Check if voting should close
- Trigger events

**Test**: Create test file

**File**: `contracts/test/JuryVoting.t.sol`

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Test.sol";
import "../src/JuryVoting.sol";

contract JuryVotingTest is Test {
    JuryVoting voting;
    address juror1 = address(0x1);
    address juror2 = address(0x2);
    address juror3 = address(0x3);

    function setUp() public {
        voting = new JuryVoting(3);
    }

    function test_InitialState() public view {
        assertEq(voting.totalJurors(), 3);
        assertEq(voting.guiltyVotes(), 0);
        assertEq(voting.notGuiltyVotes(), 0);
        assertEq(voting.votingClosed(), false);
    }

    function test_Vote() public {
        vm.prank(juror1);
        voting.vote(true); // guilty

        assertEq(voting.guiltyVotes(), 1);
        assertEq(voting.hasVoted(juror1), true);
    }

    function test_CannotVoteTwice() public {
        vm.prank(juror1);
        voting.vote(true);

        vm.prank(juror1);
        vm.expectRevert("Already voted");
        voting.vote(false);
    }

    function test_VotingCloses() public {
        vm.prank(juror1);
        voting.vote(true);
        vm.prank(juror2);
        voting.vote(true);
        vm.prank(juror3);
        voting.vote(false);

        assertEq(voting.votingClosed(), true);
    }
}
```

**Test Command**:
```bash
forge test -vv
```

**Acceptance Criteria**: All 4 tests pass

---

### Task 1.3: Implement getVoteState and getVerdict

**File**: `contracts/src/JuryVoting.sol`

**Test**: Add to test file

```solidity
function test_GetVoteState() public {
    vm.prank(juror1);
    voting.vote(true);

    (uint g, uint ng, uint total, bool closed) = voting.getVoteState();
    assertEq(g, 1);
    assertEq(ng, 0);
    assertEq(total, 1);
    assertEq(closed, false);
}

function test_GetVerdict_Guilty() public {
    vm.prank(juror1);
    voting.vote(true);
    vm.prank(juror2);
    voting.vote(true);
    vm.prank(juror3);
    voting.vote(false);

    string memory verdict = voting.getVerdict();
    assertEq(verdict, "GUILTY");
}

function test_GetVerdict_NotGuilty() public {
    vm.prank(juror1);
    voting.vote(false);
    vm.prank(juror2);
    voting.vote(false);
    vm.prank(juror3);
    voting.vote(true);

    string memory verdict = voting.getVerdict();
    assertEq(verdict, "NOT_GUILTY");
}

function test_GetVerdict_RevertsIfNotClosed() public {
    vm.expectRevert("Voting not closed");
    voting.getVerdict();
}
```

**Test Command**:
```bash
forge test -vv
```

**Acceptance Criteria**: All 8 tests pass

---

### Task 1.4: Local Deployment Testing

**Testing Method**:
```bash
# Terminal 1: Start local chain
anvil

# Terminal 2: Deploy
export PRIVATE_KEY=0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
forge script script/Deploy.s.sol --broadcast --rpc-url http://127.0.0.1:8545
```

**Acceptance Criteria**:
- See "JuryVoting deployed at: 0x..."
- Record contract address for later use

---

## Phase 2: Backend Basics (Day 1 Afternoon)

### Task 2.1: Implement VotingTool._init_web3

**File**: `backend/tools/voting_tool.py`

**Prerequisites**:
```bash
cd ai-trial-game/backend
pip install -r requirements.txt
```

**Implementation Requirements**:
```python
def _init_web3(self) -> None:
    from web3 import Web3

    self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))

    # Contract ABI (from forge compilation output, simplified here)
    abi = [
        {"inputs": [{"name": "_totalJurors", "type": "uint256"}], "stateMutability": "nonpayable", "type": "constructor"},
        {"inputs": [{"name": "guilty", "type": "bool"}], "name": "vote", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
        {"inputs": [], "name": "getVoteState", "outputs": [{"name": "", "type": "uint256"}, {"name": "", "type": "uint256"}, {"name": "", "type": "uint256"}, {"name": "", "type": "bool"}], "stateMutability": "view", "type": "function"},
        {"inputs": [], "name": "getVerdict", "outputs": [{"name": "", "type": "string"}], "stateMutability": "view", "type": "function"},
        {"inputs": [], "name": "guiltyVotes", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
        {"inputs": [], "name": "notGuiltyVotes", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
        {"inputs": [], "name": "votingClosed", "outputs": [{"name": "", "type": "bool"}], "stateMutability": "view", "type": "function"},
    ]

    self.contract = self.web3.eth.contract(
        address=self.contract_address,
        abi=abi
    )
```

**Test**: Create test file

**File**: `backend/tests/test_voting_tool.py`

```python
"""
VotingTool tests

Prerequisites: anvil running, contract deployed
"""
import pytest
from tools.voting_tool import VotingTool

# Use actual deployed contract address
CONTRACT_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa3"  # Replace with actual address

@pytest.fixture
def voting_tool():
    # anvil default private keys
    private_keys = [
        "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
        "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d",
        "0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a",
    ]
    return VotingTool(CONTRACT_ADDRESS, private_keys=private_keys)

def test_init(voting_tool):
    """Test initialization"""
    assert voting_tool.web3 is not None
    assert voting_tool.contract is not None

def test_get_vote_state(voting_tool):
    """Test get vote state"""
    state = voting_tool.get_vote_state()
    assert hasattr(state, 'guilty_votes')
    assert hasattr(state, 'not_guilty_votes')
```

**Test Command**:
```bash
cd backend
python -m pytest tests/test_voting_tool.py -v
```

**Acceptance Criteria**: Tests pass

---

### Task 2.2: Implement VotingTool Complete Functionality

**File**: `backend/tools/voting_tool.py`

**Implement**: get_vote_state, cast_vote, get_verdict

**Test**: Add to test file

```python
def test_cast_vote(voting_tool):
    """Test voting (Note: changes on-chain state)"""
    # This test will actually vote, need to redeploy contract for each run
    tx_hash = voting_tool.cast_vote(0, True)  # juror 0 votes guilty
    assert tx_hash is not None
    assert tx_hash.startswith("0x")
```

**Acceptance Criteria**: Can successfully send transaction and return hash

---

### Task 2.3: Implement Basic FastAPI Endpoints

**File**: `backend/main.py`

**Implement**: root, get_game_state (return mock data first)

**Test Command**:
```bash
cd backend
uvicorn main:app --reload

# Another terminal
curl http://localhost:8000/
curl http://localhost:8000/state
```

**Acceptance Criteria**:
- `/` returns `{"status": "ok", "game": "AI Trial"}`
- `/state` returns game state JSON

---

## Phase 3: Agent Core (Day 2 Morning)

### Task 3.1: Implement JurorAgent._load_config

**File**: `backend/agents/juror_agent.py`

**Prerequisites**: Create test character card

**File**: `content/jurors/test_juror.json`

```json
{
  "id": "test_juror",
  "name": "Test Juror",
  "background": "This is a test character",
  "personality": ["test personality"],
  "speaking_style": "test style",
  "initial_stance": 0,
  "topic_weights": {
    "technical_responsibility": 10,
    "emotional_appeal": -5
  },
  "first_message": "Hello, I am a test juror."
}
```

**Test File**: `backend/tests/test_juror_agent.py`

```python
import pytest
from agents.juror_agent import JurorAgent

def test_load_config():
    """Test loading character card"""
    agent = JurorAgent("test_juror", content_path="../content/jurors")

    assert agent.config is not None
    assert agent.config.name == "Test Juror"
    assert agent.stance_value == 0

def test_get_first_message():
    """Test getting first message"""
    agent = JurorAgent("test_juror", content_path="../content/jurors")

    msg = agent.get_first_message()
    assert msg == "Hello, I am a test juror."
```

**Test Command**:
```bash
python -m pytest tests/test_juror_agent.py::test_load_config -v
```

**Acceptance Criteria**: Tests pass

---

### Task 3.2: Implement JurorAgent._build_system_prompt

**File**: `backend/agents/juror_agent.py`

**Test**:
```python
def test_build_system_prompt():
    """Test building system prompt"""
    agent = JurorAgent("test_juror", content_path="../content/jurors")

    prompt = agent._build_system_prompt()

    assert "Test Juror" in prompt
    assert "test character" in prompt
    assert "neutral" in prompt or "stance" in prompt
```

**Acceptance Criteria**: prompt contains character information

---

### Task 3.3: Implement JurorAgent._init_llm and chat

**File**: `backend/agents/juror_agent.py`

**Environment Variables**: Create `.env` file
```
ANTHROPIC_API_KEY=your_api_key_here
```

**Implementation Points**:
```python
def _init_llm(self) -> None:
    import anthropic
    from dotenv import load_dotenv
    import os

    load_dotenv()
    self.llm_client = anthropic.Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )

async def chat(self, player_message: str) -> dict:
    # Build messages
    messages = []
    for turn in self.conversation_history:
        messages.append({"role": "user", "content": turn.player})
        messages.append({"role": "assistant", "content": turn.juror})
    messages.append({"role": "user", "content": player_message})

    # Call Claude
    response = self.llm_client.messages.create(
        model="claude-3-haiku-20240307",  # Use cheaper model for testing
        max_tokens=1024,
        system=self._build_system_prompt(),
        messages=messages
    )

    reply = response.content[0].text

    # Parse topics
    topics, impact = self._parse_topics(reply)

    # Update stance
    self._update_stance(topics, impact)

    # Clean reply
    clean_reply = self._clean_reply(reply)

    # Record history
    self.conversation_history.append(ConversationTurn(
        player=player_message,
        juror=clean_reply
    ))

    return {
        "reply": clean_reply,
        "juror_id": self.juror_id
    }
```

**Test**:
```python
import asyncio

def test_chat_integration():
    """Integration test: actually call LLM"""
    agent = JurorAgent("test_juror", content_path="../content/jurors")

    result = asyncio.run(agent.chat("Hello"))

    assert "reply" in result
    assert len(result["reply"]) > 0
    print(f"Agent reply: {result['reply']}")
```

**Test Command**:
```bash
python -m pytest tests/test_juror_agent.py::test_chat_integration -v -s
```

**Acceptance Criteria**: Can receive LLM reply

---

### Task 3.4: Implement Topic Parsing and Stance Update

**File**: `backend/agents/juror_agent.py`

**Implement**: _parse_topics, _update_stance, _clean_reply

**Test**:
```python
def test_update_stance():
    """Test stance update"""
    agent = JurorAgent("test_juror", content_path="../content/jurors")

    initial = agent.stance_value
    agent._update_stance(["technical_responsibility"], "positive")

    assert agent.stance_value == initial + 10  # topic_weights["technical_responsibility"] = 10

def test_update_stance_negative():
    """Test negative topic"""
    agent = JurorAgent("test_juror", content_path="../content/jurors")

    initial = agent.stance_value
    agent._update_stance(["emotional_appeal"], "positive")

    assert agent.stance_value == initial - 5  # topic_weights["emotional_appeal"] = -5
```

**Acceptance Criteria**: Stance value updates correctly

---

## Phase 4: Complete API Implementation (Day 2 Afternoon)

### Task 4.1: Implement AgentManager

**File**: `backend/services/agent_manager.py`

**Test**:
```python
def test_agent_manager():
    manager = AgentManager(["test_juror"])
    manager.load_all_jurors("../content/jurors")

    assert "test_juror" in manager.agents

def test_collect_votes():
    manager = AgentManager(["test_juror"])
    manager.load_all_jurors("../content/jurors")

    # Manually set stance for testing
    manager.agents["test_juror"].stance_value = 50

    votes = manager.collect_votes()
    assert votes["verdict"] == "NOT_GUILTY"
```

**Acceptance Criteria**: Tests pass

---

### Task 4.2: Implement Complete API Endpoints

**File**: `backend/main.py`

**Implement all endpoints**

**Test**: Create API tests

**File**: `backend/tests/test_api.py`

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200

def test_get_jurors():
    response = client.get("/jurors")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_dossier():
    response = client.get("/content/dossier")
    assert response.status_code == 200

def test_chat():
    response = client.post(
        "/chat/test_juror",
        json={"message": "Hello"}
    )
    assert response.status_code == 200
    assert "reply" in response.json()
```

**Test Command**:
```bash
python -m pytest tests/test_api.py -v
```

**Acceptance Criteria**: All API tests pass

---

## Phase 5: Frontend Implementation (Day 3)

### Task 5.1: Implement api.js

**File**: `frontend/js/api.js`

**Implement all API call functions**

**Testing Method**:
1. Start backend: `uvicorn main:app --reload`
2. Open browser console
3. Add test code in `index.html`:

```html
<script>
async function testAPI() {
    console.log("Test getGameState:", await getGameState());
    console.log("Test getJurors:", await getJurors());
    console.log("Test getDossier:", await getDossier());
}
testAPI();
</script>
```

**Acceptance Criteria**: Console shows correct API responses

---

### Task 5.2: Implement dialogue.js

**File**: `frontend/js/dialogue.js`

**Test**:
```javascript
// Test in console
await loadWitness("test_witness");
console.log(getCurrentNode());
selectOption("node_a");
console.log(getCurrentNode());
```

**Acceptance Criteria**: Dialogue tree can navigate correctly

---

### Task 5.3: Implement game.js Core Flow

**File**: `frontend/js/game.js`

**Step-by-step Implementation**:

1. **initGame + enterInvestigation**
   - Acceptance: Page shows investigation phase after loading

2. **showDossier + showEvidenceList**
   - Acceptance: Can view dossier and evidence

3. **startWitnessDialogue + renderDialogueNode**
   - Acceptance: Can dialogue with witnesses

4. **enterPersuasion + selectJuror**
   - Acceptance: Can switch to persuasion phase, select jurors

5. **sendMessageToJuror**
   - Acceptance: Can send messages and receive replies

6. **enterVerdict + showVerdict**
   - Acceptance: Can view voting results

**Testing Method for Each Step**:
- Open `index.html`
- Manual operation to test functionality
- Check console for no errors

---

## Phase 6: Integration Testing (Day 3 Afternoon)

### Task 6.1: End-to-End Testing

**Test Process**:

```
1. Start anvil
2. Deploy contract (record address)
3. Update contract address in backend config
4. Start backend
5. Open frontend
6. Execute complete game flow:
   - Read dossier ✓
   - View evidence ✓
   - Dialogue with witnesses ✓
   - Present evidence ✓
   - Enter persuasion phase ✓
   - Dialogue with jurors (at least 3 rounds) ✓
   - Enter trial ✓
   - View voting results ✓
```

**Acceptance Criteria**: Complete flow without errors, can see final verdict

---

### Task 6.2: Boundary Testing

**Test Items**:
- [ ] Empty message sending
- [ ] Rapid consecutive message sending
- [ ] State after page refresh
- [ ] Error handling for incorrect contract address
- [ ] API timeout handling

---

## Checklist

### Must Complete by End of Day 1
- [ ] Contract compiles
- [ ] All contract tests pass (8 total)
- [ ] Contract can be deployed to anvil
- [ ] VotingTool can connect to contract
- [ ] FastAPI can start

### Must Complete by End of Day 2
- [ ] JurorAgent can load character cards
- [ ] JurorAgent can dialogue with LLM
- [ ] Stance tracking works
- [ ] All API endpoints can respond

### Must Complete by End of Day 3
- [ ] Frontend can load
- [ ] Frontend can call backend API
- [ ] Complete game flow works
- [ ] Voting results can be displayed

---

## Common Issues

### Issue: forge command not found
```bash
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

### Issue: Python import errors
```bash
cd backend
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

### Issue: CORS errors
Check CORS configuration in `main.py`

### Issue: Contract call fails
1. Check if anvil is running
2. Check if contract address is correct
3. Check if private key has balance

### Issue: LLM call fails
1. Check API_KEY in `.env`
2. Check network connection
3. Try using haiku model to reduce cost
