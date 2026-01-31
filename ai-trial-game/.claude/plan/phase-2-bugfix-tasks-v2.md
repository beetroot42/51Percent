# Phase 2 Bug 修复任务书 v2

> 生成时间: 2026-01-30
> 来源: 多模型代码审查 (Codex + Gemini) - 第二轮
> 问题描述: 无法出示证物、无返回按键、无法与丹尼尔沟通

---

## 关键问题 (Critical) - 必须修复

### C1: 模态框嵌套在 hidden 父元素内

**优先级**: P0 - 阻断性
**来源**: Gemini + Codex 交叉验证
**位置**: `frontend/index.html:213-251`

**问题描述**:
`witness-dialogue-modal` 和 `evidence-selector-modal` 被错误嵌套在 `verification-panel.hidden` 内部。由于父元素 `verification-panel` 默认是 `hidden`，即使子模态框移除自身的 `hidden` 类也无法显示。

**当前结构** (错误):
```html
<div class="verification-panel hidden" id="verification-panel">
    <div class="verification-body">
        <div class="verification-content hidden" id="verification-content">
            <!-- 错误！这些模态框在 hidden 的父元素内 -->
            <div id="witness-dialogue-modal" class="modal hidden">...</div>
            <div id="evidence-selector-modal" class="modal hidden">...</div>
        </div>
    </div>
</div>
```

**修复方案**:
将两个模态框移到 `#app` 直接子级，与其他 section 平级：

```html
</section> <!-- 关闭 verdict-phase -->

<!-- 当事人对话弹窗 - 移到 #app 直接子级 -->
<div id="witness-dialogue-modal" class="modal hidden">
    <div class="modal-content">
        <div id="witness-portrait"></div>
        <div id="witness-text"></div>

        <!-- Daneel Chat Interface -->
        <div id="daneel-chat-container" class="hidden">
            <div id="daneel-chat-history"></div>
            <div class="chat-input-row" style="display:flex; gap:10px; margin-top:15px;">
                <input type="text" id="daneel-input" class="mono-input" placeholder="Interrogate the accused..." style="flex:1;">
                <button id="daneel-send-btn" class="mono-btn">SEND</button>
            </div>
        </div>

        <div id="dialogue-options"></div>
        <div class="modal-actions">
            <button id="show-evidence-btn" class="mono-btn">出示证物</button>
            <button id="close-dialogue-btn" class="mono-btn">结束对话</button>
        </div>
    </div>
</div>

<!-- 证物选择弹窗 - 移到 #app 直接子级 -->
<div id="evidence-selector-modal" class="modal hidden">
    <div class="modal-content">
        <h3>选择要出示的证物</h3>
        <div id="evidence-selector-grid"></div>
        <div class="modal-actions">
            <button id="cancel-evidence-btn" class="mono-btn">取消</button>
        </div>
    </div>
</div>

<!-- 链上验证面板 - 只保留验证相关内容 -->
<div class="verification-panel hidden" id="verification-panel">
    <div class="verification-header">...</div>
    <div class="verification-body">
        <div class="loading-spinner" id="verification-loading">...</div>
        <div class="verification-content hidden" id="verification-content">
            <!-- 只保留验证相关的 DOM -->
        </div>
    </div>
</div>
```

**验收标准**:
- [ ] 点击证人卡片后，证人对话模态框正常显示
- [ ] 点击"出示证物"按钮后，证物选择模态框正常显示
- [ ] 点击 Daneel 卡片后，Daneel 聊天界面正常显示

---

### C2: session_id 未初始化

**优先级**: P0 - 阻断性
**来源**: Codex
**位置**: `frontend/js/game.js:14, 156`, `frontend/js/api.js:110`

**问题描述**:
`gameState.sessionId` 仅在序章流程 (`renderPrologue`) 中通过 `getOpening()` 初始化。如果用户直接进入调查阶段（跳过序章），`sessionId` 为 `null`，导致：
1. Daneel 聊天 API 返回 404/422
2. 证物出示 API 返回 404/422
3. 证物详情 API 返回 400

**当前代码** (`game.js:initGame`):
```javascript
async function initGame() {
    // ...
    if (gameState.phase === PHASES.PROLOGUE) {
        await renderPrologue();  // 这里会初始化 sessionId
    } else {
        // 直接进入调查阶段，sessionId 未初始化！
        await enterInvestigation();
    }
}
```

**修复方案** (`game.js:enterInvestigation`):
```javascript
async function enterInvestigation() {
    // 确保有 session
    if (!gameState.sessionId) {
        try {
            const opening = await getOpening();
            gameState.sessionId = opening.session_id;
        } catch (e) {
            console.error('Failed to initialize session:', e);
            showError('无法初始化会话');
            return;
        }
    }

    gameState.phase = PHASES.INVESTIGATION;
    await setPhase(PHASES.INVESTIGATION);
    updatePhaseIndicator('调查阶段');
    showSection('investigation-phase');
    await showDossier();
}
```

**验收标准**:
- [ ] 直接进入调查阶段时，sessionId 自动初始化
- [ ] Daneel 聊天功能正常工作
- [ ] 证物出示功能正常工作
- [ ] 控制台无 404/422 错误

---

## 主要问题 (Major)

### M1: 缺少返回/后退按钮

**优先级**: P1
**来源**: Gemini
**位置**: `frontend/index.html:233-236`

**问题描述**:
证人对话模态框只有"出示证物"和"结束对话"两个按钮，缺少"返回"选项。用户无法回退到上一个对话节点，只能完全退出对话。

**当前代码**:
```html
<div class="modal-actions">
    <button id="show-evidence-btn" class="mono-btn">出示证物</button>
    <button id="close-dialogue-btn" class="mono-btn">结束对话</button>
</div>
```

**修复方案** (`index.html`):
```html
<div class="modal-actions">
    <button id="back-dialogue-btn" class="mono-btn">返回</button>
    <button id="show-evidence-btn" class="mono-btn">出示证物</button>
    <button id="close-dialogue-btn" class="mono-btn">结束对话</button>
</div>
```

**修复方案** (`game.js:bindEvents`):
```javascript
// 添加事件绑定
document.getElementById('back-dialogue-btn')?.addEventListener('click', handleDialogueBack);
```

**修复方案** (`dialogue.js` - 添加历史记录):
```javascript
const dialogueState = {
    currentWitness: null,
    currentNode: null,
    dialogueTree: null,
    unlockedClues: [],
    shownEvidence: [],
    history: [],  // 新增：对话历史栈
};

function selectOption(nextNodeId) {
    const dialogues = dialogueState.dialogueTree?.dialogues || [];
    const targetNode = dialogues.find(d => d.id === nextNodeId);
    if (targetNode) {
        // 保存当前节点到历史
        if (dialogueState.currentNode) {
            dialogueState.history.push(dialogueState.currentNode);
        }
        dialogueState.currentNode = nextNodeId;
        // ...
    }
}
```

**修复方案** (`game.js` - 添加返回处理):
```javascript
function handleDialogueBack() {
    if (dialogueState.history && dialogueState.history.length > 0) {
        dialogueState.currentNode = dialogueState.history.pop();
        renderDialogueNode();
    } else {
        // 已经是第一个节点，可以选择关闭对话或提示
        showError('已经是第一个对话节点');
    }
}
```

**验收标准**:
- [ ] 证人对话模态框显示"返回"按钮
- [ ] 点击"返回"可回到上一个对话节点
- [ ] 在第一个节点点击"返回"有适当提示

---

### M2: Daneel 内存跨会话共享

**优先级**: P1
**来源**: Codex
**位置**: `backend/agents/daneel_agent.py:28`

**问题描述**:
`DaneelAgent.memory` 是进程级全局变量，不同会话间的对话上下文会泄漏。这会导致：
1. 隐私问题：用户 A 的对话可能被用户 B 看到
2. 行为异常：Daneel 的回复会受到其他会话的影响
3. 内存增长：memory 无限增长

**当前代码**:
```python
class DaneelAgent:
    def __init__(self, content_root: Path) -> None:
        # ...
        self.memory = Memory()  # 进程级全局内存
```

**修复方案** (方案 A - per-session 内存):
```python
class DaneelAgent:
    def __init__(self, content_root: Path) -> None:
        # ...
        self._session_memories: dict[str, Memory] = {}  # session_id -> Memory

    def _get_memory(self, session_id: str) -> Memory:
        if session_id not in self._session_memories:
            self._session_memories[session_id] = Memory()
        return self._session_memories[session_id]

    async def chat(self, message: str, session_id: str) -> str:
        memory = self._get_memory(session_id)
        await memory.add_message("user", message)
        reply = await self.llm.ask(messages=memory.messages, system_msg=self.system_prompt)
        # ...
```

**修复方案** (方案 B - 重置内存):
在 `reset_game` 时清空 Daneel 内存：
```python
# main.py
@app.post("/reset")
async def reset_game():
    agent_manager.reset_all()
    daneel_agent.memory = Memory()  # 重置 Daneel 内存
    set_game_phase("prologue")
    return {"status": "reset", "phase": get_game_phase()}
```

**验收标准**:
- [ ] 不同会话的 Daneel 对话相互隔离
- [ ] 重置游戏后 Daneel 内存清空

---

### M3: 模态框焦点管理缺失

**优先级**: P2
**来源**: Gemini
**位置**: `frontend/js/game.js:startWitnessDialogue, showEvidenceSelector`

**问题描述**:
打开模态框时焦点未移动到模态框内部，关闭时焦点未还原到触发按钮。键盘用户打开弹窗后焦点仍在底层页面。

**修复方案**:
```javascript
let lastFocusedElement = null;

function openModal(modalId) {
    lastFocusedElement = document.activeElement;
    const modal = document.getElementById(modalId);
    modal?.classList.remove('hidden');

    // 聚焦到模态框内第一个可聚焦元素
    const focusable = modal?.querySelector('button, input, [tabindex="0"]');
    focusable?.focus();
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    modal?.classList.add('hidden');

    // 还原焦点
    lastFocusedElement?.focus();
    lastFocusedElement = null;
}
```

**验收标准**:
- [ ] 打开模态框后焦点在模态框内
- [ ] 关闭模态框后焦点回到触发按钮

---

## 次要问题 (Minor)

### m1: Daneel 聊天使用内联样式

**优先级**: P3
**来源**: Gemini
**位置**: `frontend/js/game.js:handleDaneelChat`

**问题描述**:
`handleDaneelChat` 使用内联样式 `style="text-align:right; color:#888;"`，破坏样式分离原则。

**修复方案**:
```javascript
// 修改前
pMsg.innerHTML = `<div class="witness-speaker" style="text-align:right; color:#888;">OVERSEER</div>...`;

// 修改后
pMsg.innerHTML = `<div class="witness-speaker message-overseer">OVERSEER</div>...`;
```

```css
/* style.css */
.message-overseer {
    text-align: right;
    color: #888;
}
```

---

### m2: witnessChat 在 sessionId 为 null 时仍发送请求

**优先级**: P3
**来源**: Codex
**位置**: `frontend/js/api.js:110`

**问题描述**:
`witnessChat` 在 `sessionId` 为 `null` 时仍会发送请求，生成 `session_id=null` 的无效 URL。

**修复方案**:
```javascript
async function witnessChat(witnessId, sessionId, body) {
    if (!sessionId) {
        throw new Error('Session ID is required');
    }
    return request(`/witness/${witnessId}/chat?session_id=${sessionId}`, {
        method: 'POST',
        body: JSON.stringify(body)
    });
}
```

---

### m3: Daneel 输入框缺少 aria-label

**优先级**: P3
**来源**: Gemini
**位置**: `frontend/index.html:225`

**问题描述**:
`#daneel-input` 仅使用 `placeholder`，缺少 `aria-label`，对屏幕阅读器用户不友好。

**修复方案**:
```html
<input type="text" id="daneel-input" class="mono-input"
       placeholder="Interrogate the accused..."
       aria-label="向丹尼尔发送消息">
```

---

### m4: Daneel LLM 调用缺少异常处理

**优先级**: P3
**来源**: Codex
**位置**: `backend/main.py:889`

**问题描述**:
`chat_with_witness` 中的 Daneel LLM 调用没有 try/except 包装，LLM 提供商错误会直接返回 500。

**修复方案**:
```python
if witness_id == "daneel":
    if not request.message:
        raise HTTPException(status_code=400, detail="message is required")
    rounds = session_manager.increment_witness_rounds(session_id, witness_id)
    if rounds > 10:
        raise HTTPException(status_code=403, detail="Daneel chat limit reached")
    try:
        reply = await daneel_agent.chat(request.message)
    except Exception as e:
        logger.error(f"Daneel chat error: {e}")
        raise HTTPException(status_code=502, detail="AI communication error")
    return WitnessNodeResponse(text=reply, is_llm=True)
```

---

## 任务优先级总览

| 优先级 | 任务 | 预估工作量 |
|--------|------|------------|
| P0 | C1 模态框位置修复 | 15 min |
| P0 | C2 session_id 初始化 | 10 min |
| P1 | M1 添加返回按钮 | 20 min |
| P1 | M2 Daneel 内存隔离 | 15 min |
| P2 | M3 焦点管理 | 20 min |
| P3 | m1-m4 次要优化 | 30 min |

---

## 修复顺序建议

1. **第一步**: 修复 C1 (模态框位置) - 这是所有问题的根本原因
2. **第二步**: 修复 C2 (session_id 初始化) - 确保 API 调用正常
3. **第三步**: 测试 Daneel 聊天和证物出示功能
4. **第四步**: 修复 M1 (返回按钮) - 改善用户体验
5. **第五步**: 修复其他次要问题
