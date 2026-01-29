[根目录](../CLAUDE.md) > **contracts**

# Contracts 模块

> Solidity 智能合约，5 人白名单陪审员投票

## 变更记录 (Changelog)

| 时间 | 操作 | 说明 |
|------|------|------|
| 2026-01-28 11:54:54 | 创建 | 初始化模块文档 |

---

## 模块职责

- 实现链上陪审员投票逻辑
- 5 个预设地址白名单机制
- 记录投票结果，不可篡改
- 自动计算判决结果

---

## 入口与启动

### 本地开发 (Anvil)

```bash
# 终端 1: 启动本地链
anvil

# 终端 2: 部署合约
cd contracts
forge script script/Deploy.s.sol --rpc-url http://127.0.0.1:8545 --broadcast
```

### Sepolia 部署

```bash
forge script script/Deploy.s.sol \
  --rpc-url https://sepolia.infura.io/v3/YOUR_KEY \
  --private-key $PRIVATE_KEY \
  --broadcast
```

---

## 对外接口

### JuryVoting.sol

```solidity
// 构造函数 - 初始化 5 个陪审员地址
constructor(address[5] memory _jurors);

// 投票 (仅白名单地址可调用)
function vote(bool guilty) external onlyJuror;

// 查询投票状态
function getVoteState() external view returns (
    uint guiltyVotes,
    uint notGuiltyVotes,
    uint totalVoted,
    bool closed
);

// 获取最终判决 (需投票已结束)
function getVerdict() external view returns (string memory);
```

### 事件

```solidity
event Voted(address indexed juror, bool guilty);
event VotingClosed(string verdict, uint guiltyVotes, uint notGuiltyVotes);
```

---

## 关键依赖与配置

### foundry.toml

```toml
[profile.default]
src = "src"
out = "out"
libs = ["lib"]
solc = "0.8.19"

[rpc_endpoints]
localhost = "http://127.0.0.1:8545"
```

### 部署环境变量

```bash
PRIVATE_KEY=0x...        # 部署者私钥
JUROR_1=0x...            # 陪审员 1 地址
JUROR_2=0x...
JUROR_3=0x...
JUROR_4=0x...
JUROR_5=0x...
```

---

## 数据模型

### 状态变量

| 变量 | 类型 | 说明 |
|------|------|------|
| `totalJurors` | uint | 固定为 5 |
| `isJuror` | mapping(address => bool) | 白名单 |
| `guiltyVotes` | uint | 有罪票数 |
| `notGuiltyVotes` | uint | 无罪票数 |
| `votingClosed` | bool | 是否已结束 |
| `hasVoted` | mapping(address => bool) | 是否已投票 |
| `votedGuilty` | mapping(address => bool) | 投票选择 |

---

## 测试与质量

```bash
forge test -vvv
```

测试用例 (`test/JuryVoting.t.sol`):
- `test_InitialState` - 初始状态检查
- `test_Vote` - 正常投票
- `test_CannotVoteTwice` - 禁止重复投票
- `test_VotingCloses` - 5 票后自动关闭
- `test_GetVerdict_Guilty` - 有罪判决
- `test_GetVerdict_NotGuilty` - 无罪判决
- `test_CannotVoteAfterClosed` - 关闭后禁止投票

---

## 常见问题 (FAQ)

**Q: 如何重新投票?**
A: 需要重新部署合约。当前合约不支持重置。

**Q: 白名单地址错误?**
A: 检查部署时的 `JUROR_1` - `JUROR_5` 环境变量。

**Q: 如何验证交易?**
A: Sepolia 使用 Etherscan，本地使用 `block-explorer.html`。

---

## 相关文件清单

| 文件 | 行数 | 说明 |
|------|------|------|
| `src/JuryVoting.sol` | 113 | 主合约 |
| `script/Deploy.s.sol` | 27 | 部署脚本 |
| `test/JuryVoting.t.sol` | 122 | Forge 测试 |
| `foundry.toml` | 9 | Foundry 配置 |
