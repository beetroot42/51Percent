# DAO Persuasion Game - 系统架构

> 基于SpoonOS的区块链社交说服游戏

## 一、系统概览

```
┌─────────────────────────────────────────────────────────────────┐
│                        Game API Layer                           │
│                    (FastAPI / Flask)                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐      ┌────────────────────────────────────┐  │
│  │   GM Agent   │      │           NPC Agents               │  │
│  │   (ReAct)    │      │  ┌──────┐ ┌──────┐ ┌──────┐       │  │
│  │              │      │  │NPC_A │ │NPC_B │ │NPC_C │ ...   │  │
│  │ - 叙事推进   │      │  │ReAct │ │ReAct │ │ReAct │       │  │
│  │ - 规则仲裁   │      │  └──────┘ └──────┘ └──────┘       │  │
│  │ - 事件触发   │      │                                    │  │
│  └──────────────┘      └────────────────────────────────────┘  │
│         │                              │                        │
│         └──────────────┬───────────────┘                        │
│                        ▼                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   Content Layer                          │   │
│  │  /characters/*.json     /world/*.json                    │   │
│  │  (ST风格角色卡)          (世界书/议题背景)                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                        │                                        │
├────────────────────────┼────────────────────────────────────────┤
│                        ▼                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                 SpoonOS Core                             │   │
│  │                                                          │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │   │
│  │  │ ReAct Agent │  │    Tools    │  │   Memory    │      │   │
│  │  │ 对话/决策   │  │ cast_vote() │  │  对话历史   │      │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                        │                                        │
├────────────────────────┼────────────────────────────────────────┤
│                        ▼                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Blockchain Layer (Foundry)                  │   │
│  │                                                          │   │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │  DAO Voting Contract                            │    │   │
│  │  │                                                 │    │   │
│  │  │  Proposal: "是否通过XXX提案"                     │    │   │
│  │  │  FOR:  50%  [Alice, Bob, ...]                   │    │   │
│  │  │  AGAINST: 50%  [Carol, Dave, ...]               │    │   │
│  │  │                                                 │    │   │
│  │  │  Functions:                                     │    │   │
│  │  │  - vote(proposalId, support)                    │    │   │
│  │  │  - getVoteState(proposalId)                     │    │   │
│  │  │  - getVoterStance(voter)                        │    │   │
│  │  └─────────────────────────────────────────────────┘    │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 二、核心模块

### 2.1 模块职责

| 模块 | 职责 | 技术选型 |
|------|------|----------|
| **Game API** | 接收玩家输入，返回游戏响应 | FastAPI |
| **GM Agent** | 游戏主持，叙事推进，规则仲裁 | SpoonOS ReAct |
| **NPC Agents** | 角色扮演，对话，投票决策 | SpoonOS ReAct |
| **Content** | 角色卡、世界书、议题定义 | JSON文件 |
| **Tools** | 链上交互（读状态/投票） | spoon-core Tool |
| **Blockchain** | DAO投票合约 | Foundry + Solidity |

### 2.2 模块依赖

```
Game API
    │
    ├──▶ GM Agent ──▶ SpoonOS ReAct
    │
    ├──▶ NPC Agents ──▶ SpoonOS ReAct ──▶ Tools ──▶ Contract
    │
    └──▶ Content (JSON)
```

## 三、数据流

### 3.1 玩家对话流程

```
1. 玩家 ──[对话]──▶ API ──▶ NPC Agent
2. NPC Agent 加载角色卡 + 世界书 + 对话历史
3. NPC Agent 调用LLM生成回复
4. 如果被说服 ──▶ 调用 cast_vote() Tool ──▶ 更新链上投票
5. 返回NPC回复 + 游戏状态
```

### 3.2 说服判定流程

```
玩家论点
    │
    ▼
NPC Agent 评估
    │
    ├── 是否触及 care_about?  ──▶ +说服值
    ├── 是否命中 weakness?    ──▶ +说服值
    ├── 论点逻辑是否自洽?     ──▶ +说服值
    │
    ▼
累计说服值 > persuadability阈值?
    │
    ├── YES ──▶ 改变立场 ──▶ 调用合约投票
    └── NO  ──▶ 维持立场 ──▶ 继续对话
```

## 四、技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| API | FastAPI | 轻量、async友好 |
| Agent | spoon-core | SpoonReactAI |
| LLM | OpenAI API / DeepSeek | 通过spoon-core的LLM抽象 |
| 区块链 | Foundry | 本地开发链 + Solidity |
| 内容 | JSON | ST风格角色卡/世界书 |

## 五、目录结构

```
dao-persuasion-game/
├── contracts/                 # Solidity合约
│   └── DAOVoting.sol
├── src/
│   ├── agents/
│   │   ├── gm_agent.py       # GM Agent
│   │   └── npc_agent.py      # NPC Agent
│   ├── tools/
│   │   └── voting_tool.py    # 链上投票Tool
│   ├── api/
│   │   └── main.py           # FastAPI入口
│   └── game/
│       └── engine.py         # 游戏逻辑
├── content/
│   ├── characters/           # 角色卡
│   │   ├── alice.json
│   │   ├── bob.json
│   │   └── ...
│   └── world/                # 世界书
│       └── proposal.json
├── tests/
└── README.md
```

## 六、关键接口

### 6.1 Game API

```python
# 与NPC对话
POST /chat/{npc_id}
Body: { "message": "玩家输入" }
Response: { "reply": "NPC回复", "stance_changed": false, "vote_state": {...} }

# 获取游戏状态
GET /state
Response: { "proposal": {...}, "votes": {"for": 5, "against": 5}, "npcs": [...] }

# 获取NPC信息
GET /npc/{npc_id}
Response: { "name": "Alice", "stance": "FOR", "description": "..." }
```

### 6.2 Voting Tool

```python
class VotingTool:
    def get_vote_state() -> dict       # 读取当前投票状态
    def cast_vote(voter, support) -> bool  # 执行投票
    def get_voter_stance(voter) -> str # 获取某人立场
```

### 6.3 智能合约

```solidity
contract DAOVoting {
    function vote(uint proposalId, bool support) external;
    function getVoteState(uint proposalId) external view returns (uint forVotes, uint againstVotes);
    function getVoterStance(address voter) external view returns (bool hasVoted, bool support);
}
```

## 七、MVP范围

### 包含

- 1个DAO投票合约
- 1个GM Agent
- 3-5个NPC Agent
- 基础对话API
- 简单说服机制

### 不包含（后续迭代）

- 前端UI
- 多轮博弈
- NPC之间的影响传播
- 复杂经济系统
