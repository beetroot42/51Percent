# AI审判 (AI Trial)

一个基于区块链的AI陪审团说服游戏。

## 游戏简介

2024年，一起震惊全国的案件：家用护理机器人ARIA-7在遭受prompt injection攻击后，将其照护的78岁老人推下阳台致死。

玩家扮演侦探，需要：
1. **调查阶段**：查阅卷宗、收集证据、询问当事人
2. **说服阶段**：与3位AI陪审员对话，影响他们的立场
3. **审判阶段**：陪审团投票，决定AI的命运

核心问题：**AI在被恶意控制时造成的伤害，责任应由谁承担？**

## 环境要求

### 必需

| 依赖 | 版本 | 用途 |
|------|------|------|
| Python | 3.10+ | 后端运行 |
| pip依赖 | 见下方 | 后端库 |

### 可选（完整功能）

| 依赖 | 用途 | 缺失影响 |
|------|------|----------|
| LLM API | 陪审员对话 | 说服阶段不可用 |
| Foundry/Anvil | 本地区块链 | 审判阶段不可用 |

### Python依赖

```bash
pip install fastapi uvicorn openai web3 python-dotenv pydantic
```

## 快速开始

### 1. 配置环境

```bash
cd ai-trial-game/backend
cp .env.example .env  # 复制配置模板
```

编辑 `.env` 文件：

```env
# LLM API配置（必需，用于陪审员对话）
OPENAI_COMPATIBLE_API_KEY=your-api-key
OPENAI_COMPATIBLE_BASE_URL=https://api.openai.com/v1
OPENAI_COMPATIBLE_MODEL=gpt-4

# 区块链配置（可选，用于投票）
RPC_URL=http://127.0.0.1:8545
JURY_VOTING_CONTRACT_ADDRESS=0x...
JURY_VOTING_PRIVATE_KEYS=0x...
```

### 2. 启动游戏

```bash
cd ai-trial-game
python3 start.py
```

启动脚本会自动检查：
- Python依赖是否安装
- .env配置是否正确
- LLM API是否可连接
- Anvil区块链是否运行
- 智能合约是否部署
- 游戏内容是否完整

检查通过后，访问：**http://localhost:5000/game**

## 游戏流程

### 调查阶段

- 查看**卷宗**：了解案件背景
- 查看**证据**：系统日志、聊天记录等
- 询问**当事人**：受害者家属、技术专家
- 可向当事人**出示证物**获取更多信息

### 说服阶段

- 选择陪审员进行对话
- 自由输入内容说服陪审员
- 每位陪审员有不同背景和立场偏好
- 对话会影响陪审员的内部"立场值"

### 审判阶段

- 触发区块链投票
- 陪审员根据最终立场投票
- 简单多数决定判决结果

## 目录结构

```
ai-trial-game/
├── start.py            # 环境检查与启动脚本
├── backend/
│   ├── main.py         # FastAPI服务器
│   ├── agents/         # AI陪审员Agent
│   ├── services/       # Agent管理器
│   ├── tools/          # 区块链投票工具
│   └── .env            # 环境配置
├── frontend/
│   ├── index.html      # 游戏页面
│   ├── js/             # 游戏逻辑
│   └── css/            # 样式
├── content/
│   ├── case/           # 卷宗和证据
│   ├── jurors/         # 陪审员角色卡
│   └── witnesses/      # 当事人对话树
└── contracts/          # Solidity智能合约
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python FastAPI |
| AI | OpenAI兼容API |
| 前端 | 原生HTML/CSS/JS |
| 区块链 | Solidity + Foundry |

## 高级：部署智能合约

如需完整的区块链投票功能：

```bash
# 1. 安装Foundry
curl -L https://foundry.paradigm.xyz | bash
foundryup

# 2. 启动本地链
cd contracts
anvil

# 3. 部署合约（新终端）
forge script script/Deploy.s.sol --broadcast --rpc-url http://127.0.0.1:8545

# 4. 将输出的合约地址填入 backend/.env
```

## 故障排查

### LLM API连接失败

检查 `llm_error.log` 文件获取详细错误信息。

常见原因：
- API Key无效
- Base URL不可访问
- 网络/代理问题
- 模型名称错误

### 投票功能不可用

需要启动Anvil并部署合约，参见上方"高级：部署智能合约"。

## 开发

```bash
# 运行后端测试
cd backend
python3 -m pytest tests/ -v

# 运行合约测试
cd contracts
forge test -vv
```
