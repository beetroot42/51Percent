# PLAN-001: 51%游戏叙事重构

> 基于 `51%游戏设计框架.md` 重构整个游戏内容和交互系统

**创建时间**: 2026-01-29
**状态**: 规划中
**参考文档**: `51%游戏设计框架.md`

---

## 总体目标

将现有技术框架（FastAPI + LLM Agent + Solidity 合约）与新的叙事设计整合：
- 第一幕：Blake任务对话系统
- 第二幕：证人对话 + 证物出示触发机制
- 第三幕：5个新陪审员 + 10轮对话限制 + 多结局

---

## Phase 0: 准备工作

### P0.1 存档当前版本
- [x] 用户自行推送到新branch存档

### P0.2 创建目录结构
- [ ] 创建 `content/story/` 目录
- [ ] 创建 `content/triggers/` 目录
- [ ] 创建 `content/prompts/` 目录
- [ ] 删除旧陪审员文件 `content/jurors/juror_*.json`
- [ ] 删除旧证人文件 `content/witnesses/*.json`
- [ ] 删除旧证据文件 `content/case/evidence/*.json`

### P0.3 创建占位符模板
- [ ] 创建所有新 JSON 文件（带占位符内容）
- [ ] 确保后端能加载新结构

---

## Phase 1: 开场 + Blake 对话

### 目标
跑通：启动游戏 → 世界观滚动 → Blake 3轮对话 → 进入调查阶段

### 后端任务

| ID | 任务 | 文件 | 依赖 |
|----|------|------|------|
| B1.1 | 新增 `/story/opening` API | `backend/main.py` | - |
| B1.2 | 新增 `/story/blake` API（返回对话树） | `backend/main.py` | - |
| B1.3 | 新增 `/story/blake/respond` API（处理选择） | `backend/main.py` | - |
| B1.4 | 新增 `prologue` 游戏阶段 | `backend/main.py` | - |

### 前端任务

| ID | 任务 | 文件 | 依赖 |
|----|------|------|------|
| F1.1 | 世界观滚动动画组件 | `frontend/js/game.js` | B1.1 |
| F1.2 | Blake 对话UI（3选项选择） | `frontend/js/game.js` | B1.2 |
| F1.3 | 对话选择交互逻辑 | `frontend/js/game.js` | B1.3 |
| F1.4 | CSS：开场样式 | `frontend/css/style.css` | - |

### 内容任务

| ID | 任务 | 文件 | 依赖 |
|----|------|------|------|
| C1.1 | 填写世界观文本 | `content/story/opening.json` | - |
| C1.2 | 填写Blake对话（3轮×3选项） | `content/story/blake.json` | - |

### 验收标准
- [ ] 启动游戏显示世界观滚动
- [ ] 滚动结束进入Blake对话
- [ ] 能完成3轮对话选择
- [ ] 对话结束自动进入调查阶段

---

## Phase 2: 调查阶段核心

### 目标
跑通：查看卷宗 → 与证人对话 → 出示证物 → 解锁新证物

### 后端任务

| ID | 任务 | 文件 | 依赖 |
|----|------|------|------|
| B2.1 | 重写 `/content/dossier` 返回新卷宗 | `backend/main.py` | - |
| B2.2 | 重写 `/content/evidence` 支持 E1-E15 | `backend/main.py` | - |
| B2.3 | 新增证物解锁状态管理 | `backend/main.py` | - |
| B2.4 | 新增 `/witness/{id}/chat` 证人对话 | `backend/main.py` | - |
| B2.5 | 新增 `/witness/{id}/present/{evidence_id}` 出示证物 | `backend/main.py` | - |
| B2.6 | 证物触发逻辑（读取 triggers.json） | `backend/services/` | B2.5 |
| B2.7 | 被告AI Agent（丹尼尔）- 混合模式 | `backend/agents/` | - |

### 前端任务

| ID | 任务 | 文件 | 依赖 |
|----|------|------|------|
| F2.1 | 证人选择面板（3人） | `frontend/js/game.js` | B2.4 |
| F2.2 | 证人对话UI（不同于陪审员） | `frontend/js/game.js` | B2.4 |
| F2.3 | 出示证物按钮/弹窗 | `frontend/js/game.js` | B2.5 |
| F2.4 | 证物解锁通知 | `frontend/js/game.js` | B2.6 |
| F2.5 | 证物面板显示锁定/解锁状态 | `frontend/js/game.js` | B2.3 |

### 内容任务

| ID | 任务 | 文件 | 依赖 |
|----|------|------|------|
| C2.1 | 重写卷宗内容 | `content/case/dossier.json` | - |
| C2.2 | 创建 E1-E10 初始证物 | `content/case/evidence/E01-E10*.json` | - |
| C2.3 | 创建 E11-E15 解锁证物 | `content/case/evidence/E11-E15*.json` | - |
| C2.4 | 创建谢顿配置+对话 | `content/witnesses/seldon.json` | - |
| C2.5 | 创建铎丝配置+对话 | `content/witnesses/dors.json` | - |
| C2.6 | 创建丹尼尔配置+prompt | `content/witnesses/daneel.json` | - |
| C2.7 | 创建触发规则 | `content/triggers/evidence_triggers.json` | - |

### 验收标准
- [ ] 能查看新卷宗内容
- [ ] 能看到 E1-E10 证物（E11-E15 锁定）
- [ ] 能与谢顿、铎丝进行预设对话
- [ ] 能与丹尼尔进行 LLM 对话
- [ ] 出示证物触发特定回应
- [ ] 满足条件时解锁新证物
- [ ] 解锁时有通知

---

## Phase 3: 陪审员系统重做

### 目标
跑通：选择陪审员 → 10轮对话 → 可出示证物 → 弱点触发 → 投票

### 后端任务

| ID | 任务 | 文件 | 依赖 |
|----|------|------|------|
| B3.1 | 新陪审员配置加载（J1-J5） | `backend/main.py` | - |
| B3.2 | 新 Agent Prompt 体系 | `backend/agents/spoon_juror_agent.py` | - |
| B3.3 | 偏差值系统（0-100） | `backend/agents/spoon_juror_agent.py` | - |
| B3.4 | 10轮对话限制 | `backend/main.py` | - |
| B3.5 | 向陪审员出示证物 | `backend/main.py` | Phase 2 |
| B3.6 | 弱点触发检测 | `backend/agents/spoon_juror_agent.py` | - |

### 前端任务

| ID | 任务 | 文件 | 依赖 |
|----|------|------|------|
| F3.1 | 新陪审员卡片UI（5人） | `frontend/js/game.js` | B3.1 |
| F3.2 | 对话轮次显示（X/10） | `frontend/js/game.js` | B3.4 |
| F3.3 | 轮次用完提示 | `frontend/js/game.js` | B3.4 |
| F3.4 | 出示证物给陪审员 | `frontend/js/game.js` | B3.5 |

### 内容任务

| ID | 任务 | 文件 | 依赖 |
|----|------|------|------|
| C3.1 | 创建 J1 理中客配置 | `content/jurors/j1_rationalist.json` | - |
| C3.2 | 创建 J2 激进者配置 | `content/jurors/j2_radical.json` | - |
| C3.3 | 创建 J3 同情者配置 | `content/jurors/j3_sympathizer.json` | - |
| C3.4 | 创建 J4 机奸配置 | `content/jurors/j4_opportunist.json` | - |
| C3.5 | 创建 J5 哲学家配置 | `content/jurors/j5_philosopher.json` | - |
| C3.6 | 创建通用 prompt 前缀 | `content/prompts/common_prefix.md` | - |
| C3.7 | 创建陪审员 prompt 后缀 | `content/prompts/juror_suffix.md` | - |

### 验收标准
- [ ] 显示5个新陪审员
- [ ] 每个陪审员有独立性格和对话风格
- [ ] 对话显示轮次 X/10
- [ ] 10轮后无法继续对话
- [ ] 可向陪审员出示证物
- [ ] 偏差值根据对话变化
- [ ] 投票结果基于偏差值（>50有罪）

---

## Phase 4: 结局系统

### 目标
跑通：投票完成 → 显示判决 → 结局文本 → Blake反应（可选）

### 后端任务

| ID | 任务 | 文件 | 依赖 |
|----|------|------|------|
| B4.1 | 新增 `/story/ending` API | `backend/main.py` | - |
| B4.2 | 结局类型判定逻辑 | `backend/main.py` | - |

### 前端任务

| ID | 任务 | 文件 | 依赖 |
|----|------|------|------|
| F4.1 | 结局展示UI | `frontend/js/game.js` | B4.1 |
| F4.2 | 不同结局不同样式 | `frontend/css/style.css` | - |

### 内容任务

| ID | 任务 | 文件 | 依赖 |
|----|------|------|------|
| C4.1 | 有罪结局文本 | `content/story/ending_guilty.json` | - |
| C4.2 | 无罪结局文本 | `content/story/ending_not_guilty.json` | - |
| C4.3 | 背叛结局文本（可选） | `content/story/ending_betrayal.json` | - |

### 验收标准
- [ ] 投票后显示判决
- [ ] 显示对应结局文本
- [ ] 结局有独特视觉效果

---

## 实施顺序建议

```
Week 1: Phase 0 + Phase 1
        ├── 创建目录结构和占位符
        ├── 开场 + Blake 对话
        └── 可以先用占位符文本跑通

Week 2: Phase 2 (核心)
        ├── 证人对话系统
        ├── 证物出示触发
        └── 被告AI混合模式

Week 3: Phase 3
        ├── 5个新陪审员
        ├── 新 prompt 体系
        └── 10轮限制 + 偏差值

Week 4: Phase 4 + 完善
        ├── 结局系统
        ├── 内容填充
        └── 测试和修复
```

---

## 技术决策记录

### D1: 被告AI对话模式
**决策**: 混合模式（LLM + 证物触发预设）
**原因**:
- 证物触发时必须输出特定内容以解锁新证物
- 非触发时保留 LLM 自由对话能力
- 符合10轮对话限制

### D2: 偏差值范围
**决策**: 改为 0-100（原 -100~100）
**原因**:
- 设计文档采用 0-100，>50 倾向有罪
- 需要修改现有 stance 系统

### D3: 证人对话模式
**决策**:
- 谢顿、铎丝：纯预设对话树（非 LLM）
- 丹尼尔：LLM + 触发预设

**原因**:
- 谢顿、铎丝的对话需要严格控制以触发证物
- 丹尼尔作为被告需要更自然的对话

### D4: Blake 对话
**决策**: 纯预设对话树，无 LLM
**原因**:
- 开场对话需要精确控制信息传递
- 3轮×3选项结构固定

---

## 待解决问题

| ID | 问题 | 状态 | 决策 |
|----|------|------|------|
| Q1 | 旧测试文件如何处理？ | 待定 | 更新或删除 |
| Q2 | 合约是否需要修改？ | 待定 | 可能不需要，5人投票逻辑不变 |
| Q3 | 背叛结局的触发条件？ | 待定 | 需要设计文档补充 |

---

## 相关文件

- 设计参考: `51%游戏设计框架.md`
- 内容位置索引: `plans/CONTENT-MAP.md`
- 项目根文档: `CLAUDE.md`
