# Phase 2: 调查阶段

## 目标

查看卷宗 → 与证人对话 → 出示证物 → 触发反应 → 解锁新证物 (E11-E15)

---

## 后端

### B2.1 修改 `/content/evidence` — 证物解锁状态

现有端点返回所有证物列表，需增加 session_id 参数，根据解锁状态标记每个证物。

```
GET /content/evidence?session_id=xxx
→ [ { id, name, locked: bool, ... }, ... ]
```

E1-E10 始终 `locked: false`，E11-E15 初始 `locked: true`，解锁后变 `false`。

### B2.2 修改 `/content/evidence/{id}` — 锁定证物不可查看

如果证物 ID 不在 `state.evidence_unlocked` 中，返回 403。

### B2.3 新增 API: `/witness/{id}/chat` — 证人对话

```
POST /witness/{witness_id}/chat?session_id=xxx
Body: { message: str }  (仅丹尼尔需要)
     或 { option_id: str }  (谢顿/铎丝对话树选项)

→ 谢顿/铎丝: { text, options[], is_llm: false, node_id }
→ 丹尼尔:     { text, is_llm: true }
```

**谢顿/铎丝**：读取 JSON 对话树，根据 `state.witness_nodes[id]` 追踪当前节点。
**丹尼尔**：转发给 DaneelAgent（LLM），有10轮对话限制。

### B2.4 新增 API: `/witness/{id}/present/{evidence_id}` — 出示证物

```
POST /witness/{witness_id}/present/{evidence_id}?session_id=xxx

→ { text, unlocks: [str], forced: bool }
```

核心逻辑：
1. 读取 `content/triggers/evidence_triggers.json`
2. 查找 `triggers[witness_id][evidence_id]`
3. 匹配 → 返回预设回应 + 解锁新证物 + `forced: true`
4. 不匹配 → 返回通用反应 + `forced: false`

### B2.5 新建 `backend/agents/daneel_agent.py` — 被告AI混合模式

```python
class DaneelAgent:
    """丹尼尔：LLM 自由对话 + 证物触发预设"""

    def __init__(self):
        self.llm = ChatBot(...)
        self.system_prompt = load_file("content/prompts/daneel.md")

    async def chat(self, message: str) -> str:
        """LLM 自由对话，10轮限制由外层控制"""
        return await self.llm.ask(message, system_prompt=self.system_prompt)

    def present_evidence(self, evidence_id: str) -> tuple[str, list[str]]:
        """证物触发：返回固定文本 + 解锁列表"""
        triggers = load_triggers()["daneel"]
        if evidence_id in triggers:
            t = triggers[evidence_id]
            return t["response"], t.get("unlocks", [])
        return "我不太理解你想让我看什么。", []
```

**关键**：出示证物走 `present_evidence()`（确定性），普通对话走 `chat()`（LLM）。

### B2.6 证物触发配置

`content/triggers/evidence_triggers.json` 结构：

```json
{
  "seldon": {
    "E1": { "response": "[占位]", "unlocks": ["E11"] }
  },
  "dors": {
    "E1": { "response": "[占位]", "unlocks": [] },
    "E2": { "response": "[占位]", "unlocks": [] },
    "E6": { "response": "[占位]", "unlocks": ["E12"] }
  },
  "daneel": {
    "E1": { "response": "[占位]", "unlocks": ["E13"] },
    "E3": { "response": "[占位]", "unlocks": ["E14"] },
    "E5": { "response": "[占位]", "unlocks": ["E15"] }
  }
}
```

### 涉及文件

| 文件 | 操作 |
|------|------|
| `backend/agents/daneel_agent.py` | **新建** |
| `backend/main.py` | 修改: 新增 witness API + 证物解锁 |
| `backend/services/session_manager.py` | 修改: 添加证物解锁方法 |

---

## 前端

### F2.1 修改证物面板 — 锁定/解锁状态

`showEvidenceList()` 改造：

```javascript
async function showEvidenceList() {
    const list = await getEvidenceList(gameState.sessionId);
    grid.innerHTML = list.map(e => `
        <div class="evidence-card ${e.locked ? 'locked' : ''}"
             data-id="${e.id}"
             onclick="${e.locked ? '' : `showEvidenceDetail('${e.id}')`}">
            ${e.locked ? '<span class="lock-icon">🔒</span>' : ''}
            <span class="evidence-name">${e.name}</span>
        </div>
    `).join('');
}
```

CSS 新增：
```css
.evidence-card.locked {
    filter: grayscale(80%);
    opacity: 0.5;
    cursor: not-allowed;
}
.evidence-card.locked .lock-icon {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 1.5rem;
}
```

### F2.2 证人面板改造 — 3人卡片

证人列表改为显示谢顿/铎丝/丹尼尔三人卡片，带角色名和身份标签。

### F2.3 证人对话 UI 分流

根据证人类型显示不同 UI：
- **谢顿/铎丝**：对话树模式（现有 `renderDialogueNode()` 适配）
- **丹尼尔**：LLM 聊天模式（类似陪审员的自由输入）

```javascript
async function startWitnessDialogue(witnessId) {
    gameState.currentWitness = witnessId;
    if (witnessId === 'daneel') {
        showDaneelChatUI();      // 自由输入框
    } else {
        showWitnessTreeUI();     // 选项按钮
        const node = await witnessChat(witnessId, gameState.sessionId);
        renderWitnessDialogueNode(node);
    }
}
```

### F2.4 出示证物交互

在证人对话中显示"出示证物"按钮：

```javascript
async function presentEvidenceToWitness(evidenceId) {
    const result = await presentEvidence(
        gameState.currentWitness, evidenceId, gameState.sessionId
    );

    // 显示证人反应
    showWitnessReaction(result.text);

    // 如果解锁了新证物
    if (result.unlocks.length > 0) {
        showUnlockNotification(result.unlocks);
        await refreshEvidenceList();
    }
}
```

### F2.5 证物解锁通知

```javascript
function showUnlockNotification(evidenceIds) {
    const toast = document.createElement('div');
    toast.className = 'unlock-toast';
    toast.innerHTML = `<span>🔓 解锁新证物: ${evidenceIds.join(', ')}</span>`;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => toast.remove(), 500);
    }, 3000);
}
```

CSS 新增：
```css
.unlock-toast {
    position: fixed;
    bottom: 24px;
    right: 24px;
    background: var(--accent-color);
    padding: 12px 24px;
    border-radius: 8px;
    animation: slide-in-right 0.4s ease-out;
    z-index: 1000;
}
```

### F2.6 修改 `api.js` — 新增 API 调用

```javascript
async function witnessChat(witnessId, sessionId, body) { ... }
async function presentEvidence(witnessId, evidenceId, sessionId) { ... }
async function getEvidenceList(sessionId) { ... }
```

### 涉及文件

| 文件 | 操作 |
|------|------|
| `frontend/js/game.js` | 修改: 证人对话分流 + 出示交互 + 解锁通知 |
| `frontend/js/dialogue.js` | 修改: 适配新对话树结构 |
| `frontend/js/api.js` | 修改: 新增 API 调用 |
| `frontend/index.html` | 修改: 丹尼尔聊天区域 |
| `frontend/css/style.css` | 修改: 锁定样式 + 解锁通知 |

---

## 内容

| 文件 | 说明 |
|------|------|
| `content/case/dossier.json` | 重写卷宗内容 |
| `content/case/evidence/E01-E15*.json` | 15个证物 (E11-E15 解锁型) |
| `content/witnesses/seldon.json` | 谢顿对话树 + 初始3问 |
| `content/witnesses/dors.json` | 铎丝对话树 + 初始3问 |
| `content/witnesses/daneel.json` | 丹尼尔配置 |
| `content/triggers/evidence_triggers.json` | 触发规则 |
| `content/prompts/daneel.md` | 被告AI prompt |

---

## 验收标准

- [ ] 证物面板显示 E1-E10 可查看、E11-E15 带锁定图标
- [ ] 点击锁定证物无响应
- [ ] 可与谢顿进行3选项对话
- [ ] 可与铎丝进行3选项对话
- [ ] 可与丹尼尔进行 LLM 自由对话
- [ ] 对话中可点击"出示证物"按钮
- [ ] 向谢顿出示 E1 → 触发反应 → 解锁 E11
- [ ] 向铎丝出示 E6 → 触发反应 → 解锁 E12
- [ ] 向丹尼尔出示 E1/E3/E5 → 各自解锁 E13/E14/E15
- [ ] 解锁时显示 Toast 通知
- [ ] 解锁后证物面板刷新，锁定图标消失
