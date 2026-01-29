[根目录](../CLAUDE.md) > **backend**

# Backend 模块

> Python FastAPI 后端服务，管理 LLM Agent 和链上投票

## 变更记录 (Changelog)

| 时间 | 操作 | 说明 |
|------|------|------|
| 2026-01-28 11:54:54 | 创建 | 初始化模块文档 |

---

## 模块职责

- 提供 REST API 供前端调用
- 管理 5 个 AI 陪审员 Agent (SpoonJurorAgent)
- 处理玩家与陪审员的对话
- 执行链上投票操作
- 提供游戏内容 (卷宗、证据、证人)

---

## 入口与启动

```bash
cd backend
pip install -r requirements.txt
python main.py
# 服务启动在 http://localhost:5000
```

环境变量配置见 `.env` 文件。

---

## 对外接口

### REST API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 健康检查 |
| `/state` | GET | 获取游戏状态 (phase, jurors) |
| `/phase/{phase}` | POST | 切换阶段 |
| `/jurors` | GET | 获取所有陪审员 |
| `/juror/{id}` | GET | 获取单个陪审员 |
| `/chat/{juror_id}` | POST | 与陪审员对话 |
| `/vote` | POST | 触发链上投票 |
| `/reset` | POST | 重置游戏 |
| `/content/dossier` | GET | 案件卷宗 |
| `/content/evidence` | GET | 证据列表 |
| `/content/evidence/{id}` | GET | 证据详情 |
| `/content/witnesses` | GET | 证人列表 |
| `/content/witness/{id}` | GET | 证人对话树 |
| `/api/votes/verification` | GET | 投票验证信息 |
| `/api/votes/verify` | POST | 重新验证投票 |
| `/api/blockchain/genesis` | GET | 创世区块信息 |

---

## 关键依赖与配置

### 依赖

| 包 | 用途 |
|-----|------|
| `fastapi` | Web 框架 |
| `uvicorn` | ASGI 服务器 |
| `openai` | LLM API |
| `web3` | 区块链交互 |
| `spoon-ai` | Agent 框架 |
| `pydantic` | 数据验证 |
| `python-dotenv` | 环境变量 |

### 环境变量 (.env)

```bash
# LLM
OPENAI_COMPATIBLE_API_KEY=xxx
OPENAI_COMPATIBLE_BASE_URL=https://api.example.com/v1
OPENAI_COMPATIBLE_MODEL=claude-sonnet-4-5-20250929

# 区块链
RPC_URL=http://127.0.0.1:8545
JURY_VOTING_CONTRACT_ADDRESS=0x...
JURY_VOTING_PRIVATE_KEYS=key1,key2,key3,key4,key5
VOTING_TX_TIMEOUT=120
VOTING_TX_CONFIRMATIONS=1
```

---

## 数据模型

### JurorConfig

```python
@dataclass
class JurorConfig:
    id: str
    name: str
    background: str
    personality: list[str]
    speaking_style: str
    initial_stance: int      # -100 到 100
    topic_weights: dict[str, int]
    first_message: str
```

### VoteState

```python
@dataclass
class VoteState:
    guilty_votes: int
    not_guilty_votes: int
    total_voted: int
    voting_closed: bool
    verdict: str | None
```

---

## 测试与质量

```bash
pytest tests/ -v
```

测试文件:
- `test_juror_agent.py` - JurorAgent 配置加载、立场更新
- `test_spoon_juror_agent.py` - SpoonOS Agent 测试
- `test_voting_tool.py` - 投票工具测试
- `test_api.py` - API 端点测试
- `test_*_integration.py` - 需要 API Key 的集成测试

---

## 常见问题 (FAQ)

**Q: 对话返回空或错误?**
A: 检查 `OPENAI_COMPATIBLE_API_KEY` 是否配置正确。

**Q: 投票失败?**
A: 确保 Anvil 运行中，且合约已部署。检查 `JURY_VOTING_CONTRACT_ADDRESS`。

**Q: 如何添加新陪审员?**
A: 在 `content/jurors/` 添加 JSON 文件，重启服务即可自动加载。

---

## 相关文件清单

| 文件 | 行数 | 说明 |
|------|------|------|
| `main.py` | 570 | FastAPI 入口，所有 API 端点 |
| `agents/spoon_juror_agent.py` | 385 | SpoonOS Agent 实现 (主用) |
| `agents/juror_agent.py` | 386 | 独立 Agent 实现 |
| `services/agent_manager.py` | 155 | Agent 管理器 |
| `tools/voting_tool.py` | 234 | 链上投票工具 |
| `tools/spoon_voting_tool.py` | 297 | SpoonOS 投票工具 |
| `pytest.ini` | 6 | pytest 配置 |
