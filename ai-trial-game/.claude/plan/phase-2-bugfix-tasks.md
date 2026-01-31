# Phase 2 Bug 修复任务书

> 生成时间: 2026-01-30
> 来源: 多模型代码审查 (Codex + Gemini)

---

## 关键问题 (Critical) - 必须修复

### C1: 卷宗数据结构不匹配

**优先级**: P0 - 阻断性
**来源**: Gemini + Codex 交叉验证
**位置**: `frontend/js/game.js:713-716`

**问题描述**:
`showDossier()` 函数尝试渲染 `data.content`，但 `dossier.json` 使用 `sections` 数组结构，导致卷宗内容完全空白。

**当前代码**:
```javascript
container.innerHTML = `
    <h2>${data.title || '案件卷宗'}</h2>
    <div class="dossier-text">${formatContent(data.content)}</div>
`;
```

**修复方案**:
```javascript
container.innerHTML = `
    <h2>${data.title || '案件卷宗'}</h2>
    ${data.summary ? `<div class="dossier-summary">${formatContent(data.summary)}</div>` : ''}
    <div class="dossier-sections">
        ${(data.sections || []).map(s => `
            <section class="dossier-section">
                <h3>${s.title}</h3>
                <div>${formatContent(s.content)}</div>
            </section>
        `).join('')}
    </div>
`;
```

**验收标准**:
- [ ] 卷宗标题正常显示
- [ ] 卷宗摘要正常显示
- [ ] 所有 4 个 section 内容完整渲染

---

### C2: 证物详情 API 缺少 session_id

**优先级**: P0 - 阻断性
**来源**: Codex
**位置**: `frontend/js/api.js:97-99`, `frontend/js/game.js:752`

**问题描述**:
`getEvidence(evidenceId)` 未传递 `session_id` 参数，但后端 `/content/evidence/{id}` 要求必传，导致所有证物访问返回 400 错误，前端显示 "ACCESS DENIED"。

**当前代码** (api.js):
```javascript
async function getEvidence(evidenceId) {
    return request(`/content/evidence/${evidenceId}`);
}
```

**修复方案** (api.js):
```javascript
async function getEvidence(evidenceId, sessionId) {
    const query = sessionId ? `?session_id=${sessionId}` : '';
    return request(`/content/evidence/${evidenceId}${query}`);
}
```

**修复方案** (game.js:752):
```javascript
// 修改前
const evidence = await getEvidence(evidenceId);

// 修改后
const evidence = await getEvidence(evidenceId, gameState.sessionId);
```

**验收标准**:
- [ ] 点击未锁定证物 (E1-E10) 可正常打开详情
- [ ] 点击锁定证物无响应或显示锁定提示
- [ ] 控制台无 400/403 错误

---

### C3: 交互元素无键盘可访问性

**优先级**: P1 - 严重
**来源**: Gemini
**位置**: `frontend/js/game.js:734, 910`

**问题描述**:
证物卡片和证人卡片使用 `div` + `onclick`，缺少 `role="button"`、`tabindex="0"`、键盘事件监听，导致键盘用户和读屏软件用户无法操作。

**当前代码** (证物卡片):
```javascript
<div class="evidence-card" onclick="showEvidenceDetail('${e.id}')">
```

**修复方案**:
```javascript
<button class="evidence-card" onclick="showEvidenceDetail('${e.id}')">
```

或保留 div 但添加 ARIA:
```javascript
<div class="evidence-card"
     role="button"
     tabindex="0"
     onclick="showEvidenceDetail('${e.id}')"
     onkeydown="if(event.key==='Enter'||event.key===' ')showEvidenceDetail('${e.id}')">
```

**验收标准**:
- [ ] Tab 键可聚焦到证物/证人卡片
- [ ] Enter/Space 键可触发点击事件
- [ ] 聚焦时有可见的焦点指示器

---

## 主要问题 (Major)

### M1: 证物锁定逻辑不一致

**优先级**: P1
**来源**: Codex
**位置**: `backend/main.py:737-739`

**问题描述**:
后端 `get_evidence_list` 在有 session 时完全忽略 JSON 文件中的 `locked` 字段，仅依赖 `state.evidence_unlocked` 集合判断。如果 `_load_initial_evidence_unlocked()` 逻辑有误，E1-E10 可能被错误锁定。

**当前代码**:
```python
locked = bool(data.get("locked", False))
if state is not None:
    locked = path.stem not in state.evidence_unlocked  # 完全覆盖 JSON 的 locked 值
```

**修复方案**:
```python
locked = bool(data.get("locked", False))
if state is not None:
    # 只有 JSON 标记为 locked=true 的证物才需要检查解锁状态
    if locked:
        locked = path.stem not in state.evidence_unlocked
```

**验收标准**:
- [ ] E1-E10 (locked: false) 始终可访问
- [ ] E11-E15 (locked: true) 初始锁定，解锁后可访问

---

### M2: 锁定证物仍显示在列表

**优先级**: P1
**来源**: Gemini
**位置**: `frontend/js/game.js:728`

**问题描述**:
前端显示所有证物（包括锁定的 E11-E15），但根据计划要求，需要对话解锁的证物在解锁前不应出现在列表中（避免剧透）。

**当前代码**:
```javascript
grid.innerHTML = list.map(e => `
    <div class="evidence-card ${e.locked ? 'locked' : ''}">
    // 所有证物都渲染，锁定的只是加了样式
```

**修复方案** (方案 A - 前端过滤):
```javascript
const visibleList = list.filter(e => !e.locked);
grid.innerHTML = visibleList.map(e => `...`).join('');
```

**修复方案** (方案 B - 后端过滤):
在 `main.py:get_evidence_list` 中添加参数 `include_locked=false`，默认不返回锁定证物。

**验收标准**:
- [ ] 初始状态只显示 E1-E10
- [ ] 解锁 E11 后，E11 出现在列表中
- [ ] 锁定证物不显示（或显示为占位符）

---

### M3: 模态框焦点管理缺失

**优先级**: P2
**来源**: Gemini
**位置**: `frontend/js/game.js:showEvidenceDetail, startWitnessDialogue`

**问题描述**:
打开模态框后焦点未移动到模态框内部，关闭后焦点未还原到触发按钮，导致键盘导航混乱。

**修复方案**:
```javascript
// 打开模态框时
modal.classList.remove('hidden');
modal.querySelector('.modal-content')?.focus();

// 关闭模态框时
modal.classList.add('hidden');
triggerButton?.focus(); // 还原焦点
```

**验收标准**:
- [ ] 打开模态框后焦点在模态框内
- [ ] Tab 键在模态框内循环（焦点陷阱）
- [ ] 关闭后焦点回到触发按钮

---

### M4: session_id 传递不一致

**优先级**: P1
**来源**: Codex
**位置**: `frontend/js/api.js:92-99`

**问题描述**:
`getEvidenceList()` 传递了 `session_id`，但 `getEvidence()` 没传，导致列表能正确显示锁定状态，但详情无法访问。

**修复方案**:
见 C2 修复方案。

**验收标准**:
- [ ] 证物列表和详情的 session_id 传递一致

---

## 次要问题 (Minor)

### m1: JSON 解析缺少异常保护

**优先级**: P3
**来源**: Codex
**位置**: `backend/main.py:get_dossier, get_evidence`

**问题描述**:
`json.loads()` 调用缺少 `try/except`，畸形 JSON 会导致 500 错误。

**修复方案**:
```python
try:
    data = json.loads(path.read_text(encoding="utf-8"))
except json.JSONDecodeError as e:
    raise HTTPException(status_code=500, detail=f"Invalid JSON: {e}")
```

---

### m2: 硬编码 Emoji 图标

**优先级**: P3
**来源**: Gemini
**位置**: `frontend/js/game.js` 多处

**问题描述**:
直接使用 Emoji (`🔒`, `📄`, `👤`) 作为图标，跨平台显示不一致，难以通过 CSS 控制样式。

**修复方案**:
使用 SVG 图标或 Icon Font 类名替代。

---

### m3: 缺乏加载状态反馈

**优先级**: P3
**来源**: Gemini
**位置**: `frontend/js/game.js` 所有 async 函数

**问题描述**:
在 `await` 数据返回前，UI 没有任何加载反馈。

**修复方案**:
```javascript
async function showDossier() {
    const container = document.getElementById('dossier-content');
    container.innerHTML = '<div class="loading">Loading...</div>';
    try {
        const data = await getDossier();
        // ...
    }
}
```

---

### m4: 证物列表全量扫描目录

**优先级**: P4
**来源**: Codex
**位置**: `backend/main.py:get_evidence_list`

**问题描述**:
每次请求都遍历目录并解析所有 JSON 文件，可考虑缓存优化。

**修复方案**:
添加内存缓存或使用 `@lru_cache` 装饰器（注意缓存失效策略）。

---

## 排查任务

### D1: 证人交互失效排查

**优先级**: P0
**来源**: 用户报告 Bug 3
**位置**: `frontend/index.html`, `frontend/js/game.js:startWitnessDialogue`

**排查步骤**:
1. 检查 `index.html` 是否包含 `id="witness-dialogue-modal"` 元素
2. 检查 `id="witness-text"` 和 `id="dialogue-options"` 元素是否存在
3. 检查 `content/witnesses/*.json` 的 `dialogues` 数组结构
4. 确认 `dialogues` 数组中有 `id: "start"` 的节点
5. 在浏览器控制台检查 `loadWitness()` 是否抛出异常

**可能原因**:
- DOM 元素 ID 不匹配
- `dialogues` 字段名拼写错误（如 `dialogue` vs `dialogues`）
- `start` 节点缺失

---

## 任务优先级总览

| 优先级 | 任务 | 预估工作量 |
|--------|------|------------|
| P0 | C1 卷宗渲染 | 10 min |
| P0 | C2 证物 session_id | 10 min |
| P0 | D1 证人交互排查 | 15 min |
| P1 | C3 键盘可访问性 | 30 min |
| P1 | M1 锁定逻辑 | 15 min |
| P1 | M2 隐藏锁定证物 | 10 min |
| P2 | M3 焦点管理 | 20 min |
| P3 | m1-m4 次要优化 | 30 min |
