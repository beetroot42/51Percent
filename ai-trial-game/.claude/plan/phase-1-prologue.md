# Phase 1: 开场 + Blake 对话

## 目标

启动游戏 → 世界观滚动 → Blake 3轮对话 → 进入调查阶段

---

## 后端

### B1.1 新建 `backend/services/session_manager.py`

会话状态管理，为整个游戏提供状态基础。

```python
class Phase(str, Enum):
    prologue = "prologue"
    investigation = "investigation"
    persuasion = "persuasion"
    verdict = "verdict"

class SessionState(BaseModel):
    session_id: str
    phase: Phase
    evidence_unlocked: set[str]          # E1-E10 初始
    witness_nodes: dict[str, str]        # witness_id -> current_node_id
    blake_round: int = 0                 # 0-3
    juror_rounds_used: dict[str, int]    # juror_id -> 已用轮次
    juror_stance: dict[str, int]         # 0-100

class SessionManager:
    _sessions: dict[str, SessionState] = {}

    def create_session(self) -> SessionState:
        ...

    def get(self, session_id: str) -> SessionState:
        ...
```

**关键设计**：
- 内存存储，不需持久化
- 初始 evidence_unlocked = {"E1"..."E10"}
- 陪审员初始 stance 从 JSON 配置读取
- 提供 `require_phase()` 阶段守卫函数

### B1.2 修改 `backend/main.py` — 新增 prologue 阶段

在 `valid_phases` 中加入 `"prologue"`，游戏初始阶段改为 `"prologue"`。

### B1.3 新增 API: `/story/opening`

```
GET /story/opening
→ 创建会话，返回 { session_id, text }
```

读取 `content/story/opening.json` 并初始化 SessionState。

### B1.4 新增 API: `/story/blake`

```
GET /story/blake?session_id=xxx
→ 返回当前轮对话节点 { round, text, options[] }
```

读取 `content/story/blake.json`，根据 `state.blake_round` 返回对应节点。

### B1.5 新增 API: `/story/blake/respond`

```
POST /story/blake/respond
Body: { session_id, option_id }
→ 返回 Blake 回应 + { response_text, next_round, phase }
```

递增 `blake_round`，满3轮后自动将 phase 切换到 `investigation`。

### 涉及文件

| 文件 | 操作 |
|------|------|
| `backend/services/session_manager.py` | **新建** |
| `backend/main.py` | 修改: 新增 API + prologue 阶段 |

---

## 前端

### F1.1 修改 `frontend/js/game.js` — 新增 PROLOGUE 阶段

```javascript
const PHASES = {
    PROLOGUE: 'prologue',        // 新增
    INVESTIGATION: 'investigation',
    PERSUASION: 'persuasion',
    VERDICT: 'verdict'
};
```

`initGame()` 改为先进入 `PROLOGUE`。新增 `gameState.sessionId` 字段。

### F1.2 新增函数: `renderPrologue()`

- 调用 `/story/opening` 获取文本 + session_id
- 将世界观文本注入滚动容器
- 启动 CSS 滚动动画
- 绑定跳过按钮
- 动画结束或跳过 → 调用 `startBlakeDialogue()`

### F1.3 新增函数: `startBlakeDialogue()` / `renderBlakeNode()` / `handleBlakeOption()`

- 调用 `/story/blake` 获取对话节点
- 渲染 Blake 头像 + 对话文本 + 3个选项按钮
- 点击选项 → 调用 `/story/blake/respond`
- 显示 Blake 回应文本
- 3轮结束 → 过渡到调查阶段

### F1.4 修改 `frontend/index.html` — 新增 prologue section

```html
<section id="prologue-phase" class="phase-section hidden">
    <div id="intro-scroller"></div>
    <div id="blake-dialogue" class="hidden">
        <div class="npc-portrait blake"></div>
        <div class="dialogue-box">
            <p id="blake-text"></p>
            <div id="blake-options"></div>
        </div>
    </div>
    <button id="skip-intro" class="btn-secondary">跳过</button>
</section>
```

### F1.5 修改 `frontend/css/style.css` — 开场样式

- 滚动动画 `.star-wars-crawl` (或打字机效果)
- Blake 对话布局 `#blake-dialogue`
- NPC 头像框 `.npc-portrait.blake`
- 选项按钮组 `#blake-options`
- 跳过按钮样式

### F1.6 修改 `frontend/js/api.js` — 新增 API 调用

```javascript
async function getOpening() { return request('/story/opening'); }
async function getBlakeNode(sessionId) { return request(`/story/blake?session_id=${sessionId}`); }
async function respondToBlake(sessionId, optionId) { ... }
```

### 涉及文件

| 文件 | 操作 |
|------|------|
| `frontend/js/game.js` | 修改: PROLOGUE 阶段 + 新函数 |
| `frontend/js/api.js` | 修改: 新增 API 调用 |
| `frontend/index.html` | 修改: prologue section |
| `frontend/css/style.css` | 修改: 开场样式 |

---

## 内容

| 文件 | 说明 | 更新位置参考 |
|------|------|--------------|
| `content/story/opening.json` | 世界观滚动文本 (占位符) | `plans/CONTENT-MAP.md` |
| `content/story/blake.json` | Blake 3轮×3选项 (占位符) | `plans/CONTENT-MAP.md` |

---

## 验收标准

- [ ] 启动游戏首先显示世界观滚动文字
- [ ] 点击"跳过"立即进入 Blake 对话
- [ ] 动画自然结束也进入 Blake 对话
- [ ] Blake 对话显示3个选项，可点击
- [ ] 每轮点击后显示 Blake 回应，然后进入下一轮
- [ ] 3轮结束后自动过渡到调查阶段
- [ ] session_id 正确创建和传递
