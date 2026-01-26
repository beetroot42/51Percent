# AI审判

基于SpoonOS的区块链陪审团说服游戏。

## 游戏简介

在未来世界，法庭陪审团采用区块链随机选取公民节点进行投票。玩家作为侦探调查一起prompt injection诱导具身智能杀人的案件，通过与陪审员对话影响最终判决。

## 目录结构

```
ai-trial-game/
├── contracts/          # Foundry智能合约
├── backend/            # Python后端
├── frontend/           # Web前端
└── content/            # 游戏内容（角色卡、对话树等）
```

## 快速开始

### 1. 启动本地链

```bash
cd contracts
anvil
```

### 2. 部署合约

```bash
forge script script/Deploy.s.sol --broadcast --rpc-url http://127.0.0.1:8545
```

### 3. 启动后端

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### 4. 打开前端

直接打开 `frontend/index.html` 或使用本地服务器。

## 技术栈

- **智能合约**: Solidity + Foundry
- **后端**: FastAPI + SpoonOS
- **LLM**: Claude API
- **前端**: 原生HTML/CSS/JS

## 开发状态

代码骨架已就绪，函数实现待填充（适合vibe-coding）。
