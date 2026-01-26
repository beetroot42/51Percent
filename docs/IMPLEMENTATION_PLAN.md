# AI审判 - 实施计划

> 5天黑客松：3天代码 + 2天内容

## 时间分配

```
Day 1 ████████████████████ 代码：合约 + 后端骨架
Day 2 ████████████████████ 代码：Agent + API完成
Day 3 ████████████████████ 代码：前端 + 联调
Day 4 ████████████████████ 内容：证物/当事人/陪审员
Day 5 ████████████████████ 内容：打磨 + Demo准备
```

---

## Day 1：合约 + 后端骨架

### 上午：Foundry合约

| 任务 | 产出 |
|------|------|
| 初始化Foundry项目 | `contracts/` 目录 |
| 编写JuryVoting合约 | `JuryVoting.sol` |
| 写测试 | 基础投票逻辑测试通过 |
| 本地部署 | anvil运行 + 合约部署 |

```bash
# 验收命令
cd contracts && forge test
anvil &
forge script script/Deploy.s.sol --broadcast --rpc-url http://127.0.0.1:8545
```

### 下午：后端骨架

| 任务 | 产出 |
|------|------|
| 初始化Python项目 | FastAPI + requirements.txt |
| 搭建spoon-core环境 | 能import spoon_ai |
| 写VotingTool | 调用合约的Tool |
| 基础API | `/state` 接口能返回数据 |

```bash
# 验收命令
cd backend && pip install -r requirements.txt
python -c "from spoon_ai import SpoonReactAI; print('OK')"
uvicorn main:app --reload
curl http://localhost:8000/state
```

### Day 1 交付物

```
contracts/
├── src/JuryVoting.sol       ✓
├── test/JuryVoting.t.sol    ✓
└── script/Deploy.s.sol      ✓

backend/
├── main.py                  ✓ (基础FastAPI)
├── tools/voting_tool.py     ✓
└── requirements.txt         ✓
```

---

## Day 2：Agent + API完成

### 上午：陪审员Agent

| 任务 | 产出 |
|------|------|
| 写JurorAgent类 | 继承SpoonReactAI |
| 加载角色卡逻辑 | 读取JSON生成prompt |
| 对话历史管理 | 使用spoon-core Memory |
| 立场追踪 | 对话后返回当前立场 |

```python
# 验收：能和一个测试陪审员对话
agent = JurorAgent("juror_a")
response = await agent.chat("我认为AI是无辜的")
print(response.reply, response.stance)
```

### 下午：完整API

| 任务 | 产出 |
|------|------|
| `/chat/{juror_id}` | 与陪审员对话 |
| `/vote` | 触发投票 |
| `/state` | 完整游戏状态 |
| 多Agent管理 | AgentManager类 |

```bash
# 验收命令
curl -X POST http://localhost:8000/chat/juror_a \
  -H "Content-Type: application/json" \
  -d '{"message": "你好"}'

curl -X POST http://localhost:8000/vote
```

### Day 2 交付物

```
backend/
├── agents/
│   └── juror_agent.py       ✓
├── services/
│   └── agent_manager.py     ✓
└── main.py                  ✓ (完整API)

content/
└── jurors/
    └── _template.json       ✓ (角色卡模板)
```

---

## Day 3：前端 + 联调

### 上午：前端UI

| 任务 | 产出 |
|------|------|
| HTML骨架 | 三个阶段页面 |
| 调查阶段UI | 卷宗/证据/当事人 |
| 说服阶段UI | 陪审员列表 + 对话框 |
| 审判阶段UI | 投票结果展示 |

### 下午：联调

| 任务 | 产出 |
|------|------|
| 前端调后端API | fetch逻辑 |
| 对话树引擎 | 当事人对话 + 出示证物 |
| 投票流程 | 触发投票→显示结果 |
| 端到端测试 | 完整流程跑通 |

### Day 3 交付物

```
frontend/
├── index.html               ✓
├── css/style.css            ✓
├── js/
│   ├── game.js              ✓ (游戏主逻辑)
│   ├── dialogue.js          ✓ (对话树引擎)
│   └── api.js               ✓ (API调用)
└── assets/                  (占位图)
```

### Day 3 验收

```
完整流程：
1. 打开页面 → 看到调查阶段
2. 阅读卷宗 → 查看证据 → 与当事人对话
3. 点击"进入说服" → 与陪审员自由对话
4. 点击"开始审判" → 看到投票结果 → 显示结局
```

---

## Day 4-5：内容创作

### Day 4：核心内容

| 任务 | 数量 |
|------|------|
| 卷宗文本 | 1份 |
| 证据 | 3-5个 |
| 当事人 | 2-3个 |
| 当事人对话树 | 每人10+节点 |
| 出示证物反应 | 每证物×每当事人 |
| 陪审员角色卡 | 3-5个 |

### Day 5：打磨 + Demo

| 任务 | 说明 |
|------|------|
| 内容测试 | 自己玩几遍 |
| Bug修复 | 修联调问题 |
| 素材补充 | 像素画/图标 |
| Demo脚本 | 准备演示流程 |
| 部署 | GitHub Pages / Vercel |

---

## 依赖关系

```
Day 1 合约 ────┐
              ├──▶ Day 2 Agent+API ──▶ Day 3 前端联调
Day 1 后端骨架─┘                              │
                                              ▼
                           Day 4-5 内容创作（可与Day 3并行开始）
```

---

## 风险点

| 风险 | 应对 |
|------|------|
| spoon-core API不熟 | 参考examples/，问文档 |
| LLM API限流 | 用便宜模型，加缓存 |
| 前端写不动 | 用最简HTML，不追求美观 |
| 内容写不完 | 先保证2当事人+3陪审员能玩 |

---

## 最小可玩版本（如果时间不够）

Day 3结束时必须能：
- 显示1个卷宗
- 和1个当事人选项对话
- 和1个陪审员Agent对话
- 触发投票看到结果

这就够demo了，其他都是锦上添花。

---

## MVP内容数量

| 内容 | 数量 |
|------|------|
| 卷宗 | 1份 |
| 证据 | 3-5个 |
| 当事人 | 3个 |
| 陪审员 | 3个 |
