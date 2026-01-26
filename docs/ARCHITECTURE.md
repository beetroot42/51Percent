# AI审判 - 系统架构

> 基于SpoonOS的区块链陪审团说服游戏

## 一、游戏背景

在某个未来，法庭陪审团采用区块链随机选取公民节点进行投票，确保公正透明。

**案件**：一起prompt injection诱导具身智能杀人案
- 核心矛盾：AI是凶手还是受害者？
- 玩家身份：侦探（中立调查者）
- 目标：通过调查形成判断，说服陪审员支持你的结论

## 二、游戏流程

```
┌─────────────────────────────────────────────────────────────┐
│                     调查阶段（传统AVG）                      │
│                                                             │
│   ┌──────────┐   ┌──────────┐   ┌──────────────────────┐   │
│   │   卷宗   │   │   证据   │   │      当事人对话      │   │
│   │  (阅读)  │   │  (查看)  │   │  选项式 + 出示证物   │   │
│   └──────────┘   └──────────┘   └──────────────────────┘   │
│                                                             │
│                  [我准备好了，进入说服阶段]                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    说服阶段（Agent对话）                     │
│                                                             │
│   ┌──────────┐   ┌──────────┐   ┌──────────┐              │
│   │ 陪审员A  │   │ 陪审员B  │   │ 陪审员C  │   ...        │
│   │  Agent   │   │  Agent   │   │  Agent   │              │
│   │(自由输入) │   │(自由输入) │   │(自由输入) │              │
│   └──────────┘   └──────────┘   └──────────┘              │
│                                                             │
│                    [结束说服，进入审判]                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      审判（链上投票）                        │
│                                                             │
│      陪审员根据被影响后的立场投票 → 51%多数决 → 结局        │
│                                                             │
│      有罪：具身智能被判定为凶手                             │
│      无罪：具身智能被判定为受害者                           │
└─────────────────────────────────────────────────────────────┘
```

## 三、系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Web 前端                               │
│                  (HTML + CSS + JS)                          │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 调查阶段 UI                          │   │
│  │  - 卷宗阅读界面                                      │   │
│  │  - 证据查看界面                                      │   │
│  │  - 当事人对话（选项式 + 出示证物按钮）               │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 说服阶段 UI                          │   │
│  │  - 陪审员列表                                        │   │
│  │  - 自由输入对话框                                    │   │
│  │  - 对话历史显示                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 审判阶段 UI                          │   │
│  │  - 投票动画/结果展示                                 │   │
│  │  - 结局画面                                          │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP API
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Game API                               │
│                     (FastAPI)                               │
│                                                             │
│  POST /chat/{juror_id}     与陪审员对话                     │
│  POST /vote                触发投票                         │
│  GET  /state               获取游戏状态                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    SpoonOS Core                             │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Juror Agents (ReAct)                    │   │
│  │                                                      │   │
│  │  每个陪审员 = 1个ReAct Agent                         │   │
│  │  - 加载角色卡（性格、立场、关心的议题）              │   │
│  │  - 记录对话历史                                      │   │
│  │  - 评估玩家论点 → 更新内心立场                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    Tools                             │   │
│  │                                                      │   │
│  │  cast_vote(juror, stance)  执行链上投票              │   │
│  │  get_vote_state()          读取投票状态              │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Blockchain (Foundry)                       │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              JuryVoting Contract                     │   │
│  │                                                      │   │
│  │  mapping(address => bool) public hasVoted;           │   │
│  │  mapping(address => bool) public votedGuilty;        │   │
│  │  uint public guiltyVotes;                            │   │
│  │  uint public notGuiltyVotes;                         │   │
│  │                                                      │   │
│  │  function vote(bool guilty) external;                │   │
│  │  function getVerdict() external view returns (bool); │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 四、核心模块

### 4.1 前端（静态内容 + API调用）

| 功能 | 实现方式 |
|------|----------|
| 卷宗/证据 | 静态JSON/Markdown渲染 |
| 当事人对话 | 对话树 + 出示证物触发 |
| 陪审员对话 | fetch调用后端Agent API |
| 投票结果 | 调用合约读取 |

### 4.2 内容层

```
/content
├── case/
│   ├── dossier.json          # 卷宗
│   └── evidence/
│       ├── cctv.json         # 证据1
│       ├── chat_log.json     # 证据2
│       └── ...
├── witnesses/                 # 当事人对话树
│   ├── victim_family.json
│   ├── ai_developer.json
│   └── ...
└── jurors/                    # 陪审员角色卡
    ├── juror_a.json
    ├── juror_b.json
    └── ...
```

### 4.3 当事人对话树结构

```json
{
  "id": "ai_developer",
  "name": "AI开发者",
  "portrait": "developer.png",
  "dialogues": [
    {
      "id": "start",
      "text": "你想问什么？",
      "options": [
        { "text": "说说那天发生了什么", "next": "that_day" },
        { "text": "你对AI的安全措施", "next": "safety" }
      ]
    },
    {
      "id": "that_day",
      "text": "那天我接到报警电话时，整个人都懵了...",
      "options": [...]
    }
  ],
  "evidence_reactions": {
    "chat_log": {
      "text": "这段对话...是有人在测试prompt注入！",
      "unlock": "injection_clue"
    },
    "cctv": {
      "text": "你看这里，AI的行为明显不正常",
      "unlock": null
    }
  }
}
```

### 4.4 陪审员角色卡结构

```json
{
  "id": "juror_a",
  "name": "老王",
  "background": "退休工程师，对技术有一定了解",
  "personality": "理性、谨慎、喜欢数据说话",
  "initial_stance": "neutral",
  "care_about": ["技术细节", "责任归属"],
  "weakness": "对情感诉求不太感冒",
  "persuadability": 50,
  "first_message": "嗯，说说你的看法吧，我听着。"
}
```

## 五、API设计

### 5.1 陪审员对话

```
POST /chat/{juror_id}
Body: { "message": "玩家输入" }
Response: {
  "reply": "陪审员回复",
  "stance": "leaning_guilty",  // neutral/leaning_guilty/leaning_not_guilty
  "conversation_id": "xxx"
}
```

### 5.2 触发投票

```
POST /vote
Response: {
  "guilty_votes": 3,
  "not_guilty_votes": 2,
  "verdict": "guilty",
  "tx_hash": "0x..."
}
```

### 5.3 游戏状态

```
GET /state
Response: {
  "phase": "investigation",  // investigation/persuasion/verdict
  "jurors": [
    { "id": "juror_a", "name": "老王", "stance": "neutral" },
    ...
  ],
  "evidence_found": ["cctv", "chat_log"],
  "unlocked_clues": ["injection_clue"]
}
```

## 六、智能合约

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract JuryVoting {
    mapping(address => bool) public hasVoted;
    mapping(address => bool) public votedGuilty;

    uint public guiltyVotes;
    uint public notGuiltyVotes;
    uint public totalJurors;

    bool public votingClosed;

    constructor(uint _totalJurors) {
        totalJurors = _totalJurors;
    }

    function vote(bool guilty) external {
        require(!hasVoted[msg.sender], "Already voted");
        require(!votingClosed, "Voting closed");

        hasVoted[msg.sender] = true;
        votedGuilty[msg.sender] = guilty;

        if (guilty) {
            guiltyVotes++;
        } else {
            notGuiltyVotes++;
        }

        if (guiltyVotes + notGuiltyVotes >= totalJurors) {
            votingClosed = true;
        }
    }

    function getVerdict() external view returns (string memory) {
        require(votingClosed, "Voting not closed");
        if (guiltyVotes > notGuiltyVotes) {
            return "GUILTY";
        }
        return "NOT_GUILTY";
    }
}
```

## 七、目录结构

```
ai-trial-game/
├── contracts/                 # Foundry项目
│   ├── src/
│   │   └── JuryVoting.sol
│   ├── test/
│   └── foundry.toml
├── backend/                   # Python后端
│   ├── main.py               # FastAPI入口
│   ├── agents/
│   │   └── juror_agent.py    # 陪审员Agent
│   ├── tools/
│   │   └── voting_tool.py    # 链上投票Tool
│   └── requirements.txt
├── frontend/                  # Web前端
│   ├── index.html
│   ├── css/
│   ├── js/
│   └── assets/               # 像素画等素材
├── content/                   # 游戏内容
│   ├── case/
│   ├── witnesses/
│   └── jurors/
└── README.md
```

## 八、MVP范围

### 包含

- 1个案件
- 3个证据
- 2个当事人（选项式对话 + 出示证物）
- 3个陪审员（Agent对话）
- 简单投票合约
- 基础Web UI

### 不包含（后续）

- 多案件
- 复杂证据链
- 陪审员之间互相影响
- 存档/读档
- 音效/动画
