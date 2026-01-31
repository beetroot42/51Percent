# Phase 3 陪审员系统 Bug 修复任务

> 生成时间: 2026-01-31
> 审查模型: Codex + Gemini 双模型交叉验证

---

## 问题概述

用户报告两个 Bug：
1. 给陪审员出示证物时提示"无法出示证物"
2. 发送消息也会报错

**API 本身没有问题**（后端能正常启动）

---

## 根因分析

### 核心问题：Session Phase 同步缺失

```
enterPersuasion()
  → setPhase("persuasion")
  → POST /phase/persuasion
  → game_phase_var = "persuasion" ✓
  → session.phase 仍然是 "investigation" ✗

chatWithJuror() / presentEvidence()
  → require_phase(state, Phase.persuasion)
  → state.phase == "investigation"
  → 400 "Invalid phase"
  → 前端显示 "TRANSMISSION ERROR" / "出示证物失败"
```

**问题链路**：
| 组件 | 文件 | 行号 | 问题 |
|------|------|------|------|
| 前端 | `frontend/js/game.js` | 524-537 | `enterPersuasion()` 调用 `setPhase()` 但不传 sessionId |
| 后端 | `backend/main.py` | 546-561 | `POST /phase/{phase_name}` 只更新全局变量，不更新 session |
| 后端 | `backend/main.py` | 600, 647 | `require_phase(state, Phase.persuasion)` 检查 session phase |

---

## 修复任务

### Task 1: 修复 Session Phase 同步 [Critical]

#### 1.1 修改后端 `set_phase` 端点

**文件**: `backend/main.py`
**行号**: 546-561

```python
# 修改前
@app.post("/phase/{phase_name}")
async def set_phase(phase_name: str):
    valid_phases = {"prologue", "investigation", "persuasion", "verdict"}
    if phase_name not in valid_phases:
        raise HTTPException(status_code=400, detail="Invalid phase")
    set_game_phase(phase_name)
    return {"phase": get_game_phase()}

# 修改后
@app.post("/phase/{phase_name}")
async def set_phase(phase_name: str, session_id: str | None = None):
    valid_phases = {"prologue", "investigation", "persuasion", "verdict"}
    if phase_name not in valid_phases:
        raise HTTPException(status_code=400, detail="Invalid phase")

    set_game_phase(phase_name)

    # 同步更新 session phase
    if session_id:
        try:
            state = session_manager.get(session_id)
            state.phase = Phase(phase_name)
        except (KeyError, ValueError):
            pass  # session 不存在或 phase 无效时静默忽略

    return {"phase": get_game_phase()}
```

#### 1.2 修改前端 `setPhase` API

**文件**: `frontend/js/api.js`
**行号**: 52-54

```javascript
// 修改前
async function setPhase(phase) {
    return request(`/phase/${phase}`, { method: 'POST' });
}

// 修改后
async function setPhase(phase, sessionId) {
    const query = sessionId ? `?session_id=${sessionId}` : '';
    return request(`/phase/${phase}${query}`, { method: 'POST' });
}
```

#### 1.3 修改前端 `enterPersuasion` 调用

**文件**: `frontend/js/game.js`
**行号**: 524-537

```javascript
// 修改前
async function enterPersuasion() {
    setLoading(true);
    try {
        gameState.phase = PHASES.PERSUASION;
        await setPhase(PHASES.PERSUASION);
        // ...
    }
}

// 修改后
async function enterPersuasion() {
    setLoading(true);
    try {
        gameState.phase = PHASES.PERSUASION;
        await setPhase(PHASES.PERSUASION, gameState.sessionId);
        // ...
    }
}
```

#### 1.4 同步修改 `enterInvestigation` 和 `enterVerdict`

**文件**: `frontend/js/game.js`

```javascript
// enterInvestigation (line 506-522)
await setPhase(PHASES.INVESTIGATION, gameState.sessionId);

// enterVerdict (line 539-598)
await setPhase(PHASES.VERDICT, gameState.sessionId);
```

---

### Task 2: 添加缺失的 `hasShownEvidence` 函数 [Critical]

**文件**: `frontend/js/game.js`
**位置**: 在 `showEvidenceSelector` 函数之前添加

```javascript
/**
 * 检查证物是否已在当前陪审员对话中出示过
 */
function hasShownEvidence(evidenceId) {
    if (!gameState.currentJuror) return false;
    const history = gameState.chatHistory[gameState.currentJuror] || [];
    return history.some(msg =>
        msg.role === 'player' &&
        msg.content?.includes(`出示证物: ${evidenceId}`)
    );
}
```

---

### Task 3: `enterPersuasion` 检查 Session 存在 [Major]

**文件**: `frontend/js/game.js`
**行号**: 524-537

```javascript
async function enterPersuasion() {
    // 添加 session 检查
    if (!gameState.sessionId) {
        showError('会话已过期，请重新开始游戏');
        await handleRestart();
        return;
    }

    setLoading(true);
    try {
        gameState.phase = PHASES.PERSUASION;
        await setPhase(PHASES.PERSUASION, gameState.sessionId);
        updatePhaseIndicator('说服阶段');
        showSection('persuasion-phase');
        await showJurorList();
    } catch (e) {
        showError('切换阶段失败');
    } finally {
        setLoading(false);
    }
}
```

---

### Task 4: 陪审员卡片添加键盘支持 [Major]

**文件**: `frontend/js/game.js`
**函数**: `showJurorList()` (line 1332-1356)

```javascript
// 修改前
container.innerHTML = realJurors.map(j => `
    <div class="juror-card ${gameState.currentJuror === j.id ? 'active' : ''}"
         data-id="${j.id}" onclick="selectJuror('${j.id}')">
        ...
    </div>
`).join('');

// 修改后
container.innerHTML = realJurors.map(j => `
    <div class="juror-card ${gameState.currentJuror === j.id ? 'active' : ''}"
         data-id="${j.id}"
         onclick="selectJuror('${j.id}')"
         onkeydown="if(event.key==='Enter'||event.key===' ')selectJuror('${j.id}')"
         role="button"
         tabindex="0">
        <span class="juror-codename">${j.codename || ''}</span>
        <span class="juror-name">${j.name || j.id}</span>
        <span class="juror-stance-hint">${j.stance_label || ''}</span>
    </div>
`).join('');
```

---

## 验收标准

- [ ] 进入说服阶段后，发送消息正常工作
- [ ] 进入说服阶段后，出示证物正常工作
- [ ] 页面刷新后进入说服阶段有友好提示
- [ ] 键盘用户可以使用 Tab + Enter 选择陪审员
- [ ] 已出示的证物有视觉区分

---

## 文件变更清单

| 文件 | 操作 | 优先级 |
|------|------|--------|
| `backend/main.py` | 修改 `set_phase` 端点 | Critical |
| `frontend/js/api.js` | 修改 `setPhase` 函数 | Critical |
| `frontend/js/game.js` | 修改 `enterPersuasion/Investigation/Verdict` | Critical |
| `frontend/js/game.js` | 添加 `hasShownEvidence` 函数 | Critical |
| `frontend/js/game.js` | 修改 `showJurorList` 添加键盘支持 | Major |

---

## 审查评分

| 评分项 | Codex | Gemini |
|--------|-------|--------|
| 根因定位 | 4/20 | 5/20 |
| 代码质量 | 10/20 | 18/20 |
| 可访问性 | - | 12/20 |
| 总分 | 28/100 | 73/100 |

**结论**: 需要修复后才能正常使用
