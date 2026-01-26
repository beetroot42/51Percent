# AI审判游戏 - Day 1 开发任务

**来源 Agent**: Gemini Antigravity  
**创建时间**: 2026-01-26 16:08  
**任务类型**: 代码生成/实现  

---

## 背景

这是一个5天黑客松项目"AI审判"，基于SpoonOS的区块链陪审团说服游戏。当前处于Day 1阶段，需要完成：
1. 智能合约实现
2. 后端基础框架

项目骨架已存在于 `d:\51-DEMO\ai-trial-game\`，但核心代码都是TODO占位符，需要实现。

---

## ⚠️ 开发注意事项（必读）

参考 `docs/spoonOS_development_pitfalls.md.resolved` 中的经验教训：

1. **虚拟环境**: 如果需要运行Python，确保使用正确的虚拟环境
2. **OpenAI Compatible Provider**: 如果使用spoon-core，注意Provider需要显式注册
3. **Base URL配置**: 只配置到 `/v1`，不要包含 `/chat/completions`
4. **测试驱动**: 每步实现后必须测试通过

---

## 任务目标

按照 `docs/CODEX_EXECUTION_GUIDE.md` 的顺序，完成以下任务：

### 阶段一：智能合约（Task 1.1 - 1.3）

**工作目录**: `d:\51-DEMO\ai-trial-game\contracts`

1. **Task 1.1**: 实现 `src/JuryVoting.sol` 的构造函数
   - 验证 `_totalJurors > 0`
   - 设置 `totalJurors`

2. **Task 1.2**: 实现 `vote` 函数
   - 检查是否已投票
   - 检查投票是否已结束
   - 记录投票状态
   - 更新票数
   - 检查是否应关闭投票
   - 触发 `Voted` 事件

3. **Task 1.3**: 实现 `getVoteState` 和 `getVerdict` 函数
   - `getVoteState`: 返回当前投票状态
   - `getVerdict`: 返回最终判决（需检查投票已结束）
   - 实现 `closeVoting` 强制结束功能

4. 创建测试文件 `test/JuryVoting.t.sol`，参考CODEX_EXECUTION_GUIDE.md中的测试代码

**验证命令**:
```bash
cd d:\51-DEMO\ai-trial-game\contracts
forge build
forge test -vv
```

**验收标准**: 所有测试通过

---

### 阶段二：后端基础（Task 2.1 - 2.3）

**工作目录**: `d:\51-DEMO\ai-trial-game\backend`

1. **Task 2.1**: 实现 `tools/voting_tool.py` 的 `_init_web3` 方法
   - 使用 web3.py 连接
   - 定义合约ABI
   - 创建合约实例

2. **Task 2.2**: 实现 `VotingTool` 完整功能
   - `get_vote_state()`: 查询投票状态
   - `cast_vote()`: 执行投票
   - `get_verdict()`: 获取判决结果

3. **Task 2.3**: 实现 `main.py` 基础端点
   - 实现 `get_game_state` 返回mock数据
   - 确保 `/` 和 `/state` 端点工作

---

## 相关文件

| 文件 | 路径 | 说明 |
|------|------|------|
| 合约 | `ai-trial-game/contracts/src/JuryVoting.sol` | 需要实现TODO |
| 合约测试 | `ai-trial-game/contracts/test/JuryVoting.t.sol` | 需要创建/实现 |
| 部署脚本 | `ai-trial-game/contracts/script/Deploy.s.sol` | 检查是否完整 |
| 投票工具 | `ai-trial-game/backend/tools/voting_tool.py` | 需要实现TODO |
| API主入口 | `ai-trial-game/backend/main.py` | 需要实现TODO |
| 执行指南 | `docs/CODEX_EXECUTION_GUIDE.md` | 详细实现参考 |
| 架构设计 | `docs/ARCHITECTURE.md` | 系统架构参考 |
| 踩坑记录 | `docs/spoonOS_development_pitfalls.md.resolved` | 开发注意事项 |

---

## 输出要求

1. 直接修改上述文件，实现所有TODO
2. 确保每个阶段的验证命令能通过
3. 将完成报告保存至: `docs/AI协作/本地Agent/进行中/2026-01-26_AI审判游戏开发/报告_AI审判Day1开发_Codex.md`

报告应包含：
- 完成的任务列表
- 遇到的问题及解决方案
- 验证结果截图/输出
- 下一步建议

---

**请开始执行。自主分析代码结构，按顺序完成任务。遇到任何问题请在报告中记录。**
