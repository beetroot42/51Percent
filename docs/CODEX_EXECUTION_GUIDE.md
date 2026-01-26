# Codex执行方案

> 按顺序执行，每步完成后必须通过测试再进入下一步

## 执行原则

1. **严格按顺序执行** - 不要跳步
2. **每步必须测试** - 测试通过才能继续
3. **遇到问题先修复** - 不要带着bug继续
4. **保持代码简洁** - 不要过度设计

---

## 阶段一：智能合约（Day 1上午）

### Task 1.1: 实现JuryVoting构造函数

**文件**: `contracts/src/JuryVoting.sol`

**实现要求**:
```solidity
constructor(uint _totalJurors) {
    require(_totalJurors > 0, "Must have at least 1 juror");
    totalJurors = _totalJurors;
}
```

**测试方法**:
```bash
cd ai-trial-game/contracts
forge build
```

**验收标准**: 编译通过，无错误

---

### Task 1.2: 实现vote函数

**文件**: `contracts/src/JuryVoting.sol`

**实现要求**:
- 检查是否已投票
- 检查投票是否已结束
- 记录投票
- 更新票数
- 检查是否应关闭投票
- 触发事件

**测试**: 创建测试文件

**文件**: `contracts/test/JuryVoting.t.sol`

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
        voting.vote(true); // 有罪

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

**测试命令**:
```bash
forge test -vv
```

**验收标准**: 所有4个测试通过

---

### Task 1.3: 实现getVoteState和getVerdict

**文件**: `contracts/src/JuryVoting.sol`

**测试**: 添加到测试文件

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

**测试命令**:
```bash
forge test -vv
```

**验收标准**: 所有8个测试通过

---

### Task 1.4: 本地部署测试

**测试方法**:
```bash
# 终端1: 启动本地链
anvil

# 终端2: 部署
export PRIVATE_KEY=0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
forge script script/Deploy.s.sol --broadcast --rpc-url http://127.0.0.1:8545
```

**验收标准**:
- 看到 "JuryVoting deployed at: 0x..."
- 记录合约地址，后续使用

---

## 阶段二：后端基础（Day 1下午）

### Task 2.1: 实现VotingTool._init_web3

**文件**: `backend/tools/voting_tool.py`

**前置准备**:
```bash
cd ai-trial-game/backend
pip install -r requirements.txt
```

**实现要求**:
```python
def _init_web3(self) -> None:
    from web3 import Web3

    self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))

    # 合约ABI（从forge编译输出获取，这里简化）
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

**测试**: 创建测试文件

**文件**: `backend/tests/test_voting_tool.py`

```python
"""
VotingTool测试

前置条件: anvil运行中，合约已部署
"""
import pytest
from tools.voting_tool import VotingTool

# 使用实际部署的合约地址
CONTRACT_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa3"  # 替换为实际地址

@pytest.fixture
def voting_tool():
    # anvil默认私钥
    private_keys = [
        "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
        "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d",
        "0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a",
    ]
    return VotingTool(CONTRACT_ADDRESS, private_keys=private_keys)

def test_init(voting_tool):
    """测试初始化"""
    assert voting_tool.web3 is not None
    assert voting_tool.contract is not None

def test_get_vote_state(voting_tool):
    """测试获取投票状态"""
    state = voting_tool.get_vote_state()
    assert hasattr(state, 'guilty_votes')
    assert hasattr(state, 'not_guilty_votes')
```

**测试命令**:
```bash
cd backend
python -m pytest tests/test_voting_tool.py -v
```

**验收标准**: 测试通过

---

### Task 2.2: 实现VotingTool完整功能

**文件**: `backend/tools/voting_tool.py`

**实现**: get_vote_state, cast_vote, get_verdict

**测试**: 添加到测试文件

```python
def test_cast_vote(voting_tool):
    """测试投票（注意：会改变链上状态）"""
    # 这个测试会实际投票，每次运行需要重新部署合约
    tx_hash = voting_tool.cast_vote(0, True)  # juror 0 投有罪
    assert tx_hash is not None
    assert tx_hash.startswith("0x")
```

**验收标准**: 能成功发送交易并返回hash

---

### Task 2.3: 实现基础FastAPI端点

**文件**: `backend/main.py`

**实现**: root, get_game_state (返回mock数据先)

**测试命令**:
```bash
cd backend
uvicorn main:app --reload

# 另一个终端
curl http://localhost:8000/
curl http://localhost:8000/state
```

**验收标准**:
- `/` 返回 `{"status": "ok", "game": "AI审判"}`
- `/state` 返回游戏状态JSON

---

## 阶段三：Agent核心（Day 2上午）

### Task 3.1: 实现JurorAgent._load_config

**文件**: `backend/agents/juror_agent.py`

**前置**: 创建测试用角色卡

**文件**: `content/jurors/test_juror.json`

```json
{
  "id": "test_juror",
  "name": "测试陪审员",
  "background": "这是一个测试角色",
  "personality": ["测试性格"],
  "speaking_style": "测试风格",
  "initial_stance": 0,
  "topic_weights": {
    "技术责任": 10,
    "情感诉求": -5
  },
  "first_message": "你好，我是测试陪审员。"
}
```

**测试文件**: `backend/tests/test_juror_agent.py`

```python
import pytest
from agents.juror_agent import JurorAgent

def test_load_config():
    """测试加载角色卡"""
    agent = JurorAgent("test_juror", content_path="../content/jurors")

    assert agent.config is not None
    assert agent.config.name == "测试陪审员"
    assert agent.stance_value == 0

def test_get_first_message():
    """测试获取开场白"""
    agent = JurorAgent("test_juror", content_path="../content/jurors")

    msg = agent.get_first_message()
    assert msg == "你好，我是测试陪审员。"
```

**测试命令**:
```bash
python -m pytest tests/test_juror_agent.py::test_load_config -v
```

**验收标准**: 测试通过

---

### Task 3.2: 实现JurorAgent._build_system_prompt

**文件**: `backend/agents/juror_agent.py`

**测试**:
```python
def test_build_system_prompt():
    """测试构建system prompt"""
    agent = JurorAgent("test_juror", content_path="../content/jurors")

    prompt = agent._build_system_prompt()

    assert "测试陪审员" in prompt
    assert "测试角色" in prompt
    assert "中立" in prompt or "立场" in prompt
```

**验收标准**: prompt包含角色信息

---

### Task 3.3: 实现JurorAgent._init_llm和chat

**文件**: `backend/agents/juror_agent.py`

**环境变量**: 创建 `.env` 文件
```
ANTHROPIC_API_KEY=your_api_key_here
```

**实现要点**:
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
    # 构建messages
    messages = []
    for turn in self.conversation_history:
        messages.append({"role": "user", "content": turn.player})
        messages.append({"role": "assistant", "content": turn.juror})
    messages.append({"role": "user", "content": player_message})

    # 调用Claude
    response = self.llm_client.messages.create(
        model="claude-3-haiku-20240307",  # 用便宜的模型测试
        max_tokens=1024,
        system=self._build_system_prompt(),
        messages=messages
    )

    reply = response.content[0].text

    # 解析话题
    topics, impact = self._parse_topics(reply)

    # 更新立场
    self._update_stance(topics, impact)

    # 清理回复
    clean_reply = self._clean_reply(reply)

    # 记录历史
    self.conversation_history.append(ConversationTurn(
        player=player_message,
        juror=clean_reply
    ))

    return {
        "reply": clean_reply,
        "juror_id": self.juror_id
    }
```

**测试**:
```python
import asyncio

def test_chat_integration():
    """集成测试：实际调用LLM"""
    agent = JurorAgent("test_juror", content_path="../content/jurors")

    result = asyncio.run(agent.chat("你好"))

    assert "reply" in result
    assert len(result["reply"]) > 0
    print(f"Agent回复: {result['reply']}")
```

**测试命令**:
```bash
python -m pytest tests/test_juror_agent.py::test_chat_integration -v -s
```

**验收标准**: 能收到LLM回复

---

### Task 3.4: 实现话题解析和立场更新

**文件**: `backend/agents/juror_agent.py`

**实现**: _parse_topics, _update_stance, _clean_reply

**测试**:
```python
def test_update_stance():
    """测试立场更新"""
    agent = JurorAgent("test_juror", content_path="../content/jurors")

    initial = agent.stance_value
    agent._update_stance(["技术责任"], "positive")

    assert agent.stance_value == initial + 10  # topic_weights["技术责任"] = 10

def test_update_stance_negative():
    """测试负面话题"""
    agent = JurorAgent("test_juror", content_path="../content/jurors")

    initial = agent.stance_value
    agent._update_stance(["情感诉求"], "positive")

    assert agent.stance_value == initial - 5  # topic_weights["情感诉求"] = -5
```

**验收标准**: 立场值正确更新

---

## 阶段四：API完整实现（Day 2下午）

### Task 4.1: 实现AgentManager

**文件**: `backend/services/agent_manager.py`

**测试**:
```python
def test_agent_manager():
    manager = AgentManager(["test_juror"])
    manager.load_all_jurors("../content/jurors")

    assert "test_juror" in manager.agents

def test_collect_votes():
    manager = AgentManager(["test_juror"])
    manager.load_all_jurors("../content/jurors")

    # 手动设置立场以测试
    manager.agents["test_juror"].stance_value = 50

    votes = manager.collect_votes()
    assert votes["verdict"] == "NOT_GUILTY"
```

**验收标准**: 测试通过

---

### Task 4.2: 实现完整API端点

**文件**: `backend/main.py`

**实现所有端点**

**测试**: 创建API测试

**文件**: `backend/tests/test_api.py`

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
        json={"message": "你好"}
    )
    assert response.status_code == 200
    assert "reply" in response.json()
```

**测试命令**:
```bash
python -m pytest tests/test_api.py -v
```

**验收标准**: 所有API测试通过

---

## 阶段五：前端实现（Day 3）

### Task 5.1: 实现api.js

**文件**: `frontend/js/api.js`

**实现所有API调用函数**

**测试方法**:
1. 启动后端: `uvicorn main:app --reload`
2. 打开浏览器控制台
3. 在 `index.html` 中添加测试代码:

```html
<script>
async function testAPI() {
    console.log("测试 getGameState:", await getGameState());
    console.log("测试 getJurors:", await getJurors());
    console.log("测试 getDossier:", await getDossier());
}
testAPI();
</script>
```

**验收标准**: 控制台显示正确的API响应

---

### Task 5.2: 实现dialogue.js

**文件**: `frontend/js/dialogue.js`

**测试**:
```javascript
// 在控制台测试
await loadWitness("test_witness");
console.log(getCurrentNode());
selectOption("node_a");
console.log(getCurrentNode());
```

**验收标准**: 对话树能正确导航

---

### Task 5.3: 实现game.js核心流程

**文件**: `frontend/js/game.js`

**分步实现**:

1. **initGame + enterInvestigation**
   - 验收: 页面加载后显示调查阶段

2. **showDossier + showEvidenceList**
   - 验收: 能看到卷宗和证据

3. **startWitnessDialogue + renderDialogueNode**
   - 验收: 能与当事人对话

4. **enterPersuasion + selectJuror**
   - 验收: 能切换到说服阶段，选择陪审员

5. **sendMessageToJuror**
   - 验收: 能发送消息并收到回复

6. **enterVerdict + showVerdict**
   - 验收: 能看到投票结果

**每步测试方法**:
- 打开 `index.html`
- 手动操作测试功能
- 检查控制台无错误

---

## 阶段六：联调测试（Day 3下午）

### Task 6.1: 端到端测试

**测试流程**:

```
1. 启动anvil
2. 部署合约（记录地址）
3. 更新后端配置中的合约地址
4. 启动后端
5. 打开前端
6. 执行完整游戏流程:
   - 阅读卷宗 ✓
   - 查看证据 ✓
   - 与当事人对话 ✓
   - 出示证物 ✓
   - 进入说服阶段 ✓
   - 与陪审员对话（至少3轮）✓
   - 进入审判 ✓
   - 查看投票结果 ✓
```

**验收标准**: 完整流程无报错，能看到最终判决

---

### Task 6.2: 边界测试

**测试项**:
- [ ] 空消息发送
- [ ] 快速连续发送消息
- [ ] 刷新页面后状态
- [ ] 合约地址错误时的错误处理
- [ ] API超时处理

---

## 检查清单

### Day 1 结束时必须完成
- [ ] 合约编译通过
- [ ] 合约测试全部通过（8个）
- [ ] 合约能部署到anvil
- [ ] VotingTool能连接合约
- [ ] FastAPI能启动

### Day 2 结束时必须完成
- [ ] JurorAgent能加载角色卡
- [ ] JurorAgent能与LLM对话
- [ ] 立场追踪功能正常
- [ ] 所有API端点能响应

### Day 3 结束时必须完成
- [ ] 前端能加载
- [ ] 前端能调用后端API
- [ ] 完整游戏流程能跑通
- [ ] 投票结果能显示

---

## 常见问题处理

### 问题: forge命令找不到
```bash
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

### 问题: Python导入错误
```bash
cd backend
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

### 问题: CORS错误
检查 `main.py` 中的 CORS 配置

### 问题: 合约调用失败
1. 检查anvil是否运行
2. 检查合约地址是否正确
3. 检查私钥是否有余额

### 问题: LLM调用失败
1. 检查 `.env` 中的 API_KEY
2. 检查网络连接
3. 尝试用haiku模型降低成本
