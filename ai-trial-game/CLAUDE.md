[根目录](../CLAUDE.md) > **ai-trial-game**

# AI Trial Game - 区块链陪审团说服游戏

> 结合 AI 角色扮演与链上投票的创新游戏

## 变更记录 (Changelog)

| 时间 | 操作 | 说明 |
|------|------|------|
| 2026-01-27 18:30:00 | 更新 | Sepolia 迁移完成，添加 AI 协作规则 |
| 2026-01-27 17:58:49 | 创建 | 初始化模块文档 |

---

## ⚠️ AI 协作规则（重要）

### Claude 的角色：规划者与协调者

**Claude 不直接写代码**，而是：
1. 分析需求，制定实施计划
2. 调用外部模型（Codex/Gemini）执行代码修改
3. 审查结果，协调迭代

### 代码执行分工

| 领域 | 负责模型 | Claude 职责 |
|------|----------|-------------|
| **后端** | Codex | 规划任务 → 调用 Codex → 审查结果 |
| **前端** | Gemini | 规划任务 → 调用 Gemini → 审查结果 |
| **合约** | Codex | 规划任务 → 调用 Codex → 审查结果 |

### 任务交互文件夹

`.claude/tasks/` 目录用于存放 agent 间的任务文档：

```
.claude/tasks/
├── frontend-sepolia-adaptation.md  # 前端 Sepolia 适配任务
├── backend-xxx.md                  # 后端任务
└── ...
```

**任务文档格式**：
- 背景说明
- 具体任务清单
- 参考实现代码
- 验收标准
- 相关文件列表

### 工作流程

```
1. 用户提需求
2. Claude 分析需求，写任务文档到 .claude/tasks/
3. Claude 调用对应模型执行任务
4. 模型返回结果，Claude 审查
5. 如有问题，迭代修正
6. 完成后更新任务状态
```

---

## 模块职责

AI Trial Game 是一款区块链陪审团说服游戏：

- **核心玩法**：玩家扮演辩护律师，说服 AI 陪审员为被告投票
- **AI 陪审员**：5 个独立的 AI Agent，有独特性格和立场
- **链上投票**：最终投票结果记录在 Sepolia 测试网，不可篡改
- **案件背景**：AI 机器人因 prompt injection 攻击导致命案

---

## 入口与启动

### 后端服务

```bash
cd backend
pip install -r requirements.txt
python main.py
# 访问 http://localhost:8080/game
```

### 智能合约（Sepolia）

```bash
cd contracts

# 编译
forge build

# 部署到 Sepolia
forge script script/Deploy.s.sol \
  --rpc-url https://sepolia.infura.io/v3/YOUR_KEY \
  --private-key $PRIVATE_KEY \
  --broadcast
```

---

## 对外接口

### REST API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/state` | GET | 获取游戏状态 |
| `/jurors` | GET | 获取陪审员列表（5 人） |
| `/phase/{phase}` | POST | 切换游戏阶段 |
| `/chat/{juror_id}` | POST | 与陪审员对话 |
| `/vote` | POST | 触发链上投票 |

### 智能合约接口

```solidity
// JuryVoting.sol - 5 人白名单投票
constructor(address[5] memory _jurors);
function vote(bool guilty) external onlyJuror;
function getVoteState() external view returns (uint, uint, uint, bool);
function getVerdict() external view returns (string memory);
```

---

## 关键依赖与配置

### Python 依赖

| 依赖 | 用途 |
|------|------|
| `fastapi` | Web 后端 |
| `uvicorn` | ASGI 服务器 |
| `openai` | LLM API 调用 |
| `web3` | 区块链交互 |
| `spoon-ai` | Agent 框架（本地依赖） |

### 环境变量

```bash
# LLM 配置
OPENAI_COMPATIBLE_API_KEY=xxx
OPENAI_COMPATIBLE_BASE_URL=https://api.example.com/v1
OPENAI_COMPATIBLE_MODEL=your-model

# Sepolia 区块链
RPC_URL=https://sepolia.infura.io/v3/YOUR_KEY
JURY_VOTING_CONTRACT_ADDRESS=0x...
JURY_VOTING_PRIVATE_KEYS=0x...,0x...,0x...,0x...,0x...

# 部署用地址
JUROR_1=0x...
JUROR_2=0x...
JUROR_3=0x...
JUROR_4=0x...
JUROR_5=0x...
```

---

## 数据模型

### 陪审员配置 (content/jurors/*.json)

当前 5 位陪审员：
- `juror_chen` - 陈教授
- `juror_liu` - 刘女士
- `juror_wang` - 王建国
- `juror_zhang` - 张敏（产品安全经理）
- `juror_li` - 李辩（公设辩护人）

```json
{
  "id": "juror_zhang",
  "name": "张敏",
  "initial_stance": -5,
  "topic_weights": {
    "安全措施": 18,
    "企业责任": 12
  },
  "first_message": "告诉我存在哪些安全措施..."
}
```

### 立场值系统

- 范围：-100 (有罪) 到 +100 (无罪)
- 投票阈值：stance > 0 投无罪，否则投有罪
- 51% 规则：3/5 票决定最终判决

---

## 目录结构

```
ai-trial-game/
├── .claude/
│   └── tasks/                # Agent 任务交互文件夹
│       └── frontend-sepolia-adaptation.md
├── backend/
│   ├── agents/
│   │   ├── juror_agent.py    # 独立 Agent 实现
│   │   └── spoon_juror_agent.py  # SpoonOS Agent 实现
│   ├── services/
│   │   └── agent_manager.py  # Agent 管理器
│   ├── tools/
│   │   └── voting_tool.py    # 链上投票工具（EIP-1559）
│   ├── main.py               # FastAPI 入口
│   └── .env                  # 环境配置
├── contracts/
│   ├── src/
│   │   └── JuryVoting.sol    # 5 人白名单投票合约
│   └── script/
│       └── Deploy.s.sol      # Sepolia 部署脚本
├── content/
│   └── jurors/               # 5 个陪审员配置
├── frontend/
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── game.js
│       └── api.js
└── start.py                  # 一键启动脚本
```

---

## 待办任务

### 前端 Sepolia 适配（待执行）

详见 `.claude/tasks/frontend-sepolia-adaptation.md`

- [ ] 陪审员列表 UI 适配 5 人
- [ ] 投票等待 UI 优化（进度步骤）
- [ ] 显示 Etherscan 交易链接
- [ ] 错误处理增强

---

## 测试与质量

### Python 测试

```bash
cd backend
pytest tests/ -v
```

### 智能合约测试

```bash
cd contracts
forge test -vvv
```

---

## 相关文件清单

| 文件 | 说明 |
|------|------|
| `backend/main.py` | FastAPI 后端入口 |
| `backend/agents/spoon_juror_agent.py` | 主要 Agent 实现 |
| `backend/tools/voting_tool.py` | 链上投票工具 |
| `contracts/src/JuryVoting.sol` | 5 人白名单投票合约 |
| `content/jurors/*.json` | 5 个陪审员配置 |
| `.claude/tasks/` | Agent 任务交互文件夹 |
