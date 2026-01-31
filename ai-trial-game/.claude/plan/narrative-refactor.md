# 51%游戏叙事重构 - 主计划

> 生成时间: 2026-01-30

## 计划文件索引

| 阶段 | 文件 | 说明 |
|------|------|------|
| Phase 0 | `phase-0-preparation.md` | 准备工作：目录结构、清理旧文件 |
| Phase 1 | `phase-1-prologue.md` | 开场 + Blake 对话 |
| Phase 2 | `phase-2-investigation.md` | 调查阶段重做 |
| Phase 3 | `phase-3-jurors.md` | 陪审员系统重做 |
| Phase 4 | `phase-4-ending.md` | 结局系统 |

## 执行顺序

```
Phase 0 (准备) ──────────────────────────────────────────►
                 │
                 ▼
Phase 1 ┌── 后端: SessionManager + Story API
        └── 前端: PROLOGUE 阶段 + 动画
                 │
                 ▼
Phase 2 ┌── 后端: 证物解锁 + 丹尼尔 Agent
        └── 前端: 锁定UI + 出示交互
                 │
                 ▼
Phase 3 ┌── 后端: 偏差值 0-100 + 轮次限制
        └── 前端: 轮次显示 + 出示按钮
                 │
                 ▼
Phase 4 ┌── 后端: 结局判定 API
        └── 前端: 多结局展示
```

## SESSION_ID (供 /ccg:execute 使用)

- CODEX_SESSION: `019c0d0a-96e2-7e82-ad56-3f4c399c09af`
- GEMINI_SESSION: `ed7136ea-1af4-4b3f-bf80-db6c67d0ac69`
