# Phase 3: 陪审员系统

## 目标

5个新陪审员 → 偏差值 0-100 → 每人10轮对话 → 可出示证物 → 弱点触发 → 投票

---

## 后端

### B3.1 修改 `backend/agents/spoon_juror_agent.py` — 偏差值改 0-100

当前系统 stance 范围 -100~+100，改为 0-100：
- `initial_stance` 从新 JSON 配置读取 (如 J1=65, J2=25 等)
- stance clamp 改为 `max(0, min(100, value))`
- `get_final_vote()` 改为 `return self.stance_value > 50`

```python
def _get_stance_description_for_value(self, stance_value: int) -> str:
    if stance_value > 80:
        return "你强烈倾向于判定有罪"
    elif stance_value > 60:
        return "你倾向于判定有罪，但仍愿意听取不同意见"
    elif stance_value > 40:
        return "你目前没有明确立场，正在权衡双方论点"
    elif stance_value > 20:
        return "你倾向于判定无罪，但仍有一些疑虑"
    else:
        return "你强烈倾向于判定无罪"

def get_final_vote(self) -> bool:
    return self.stance_value > 50
```

### B3.2 修改 `backend/agents/spoon_juror_agent.py` — 新 Prompt 体系

从文件加载 prompt 组件：
```python
def _build_roleplay_prompt(self, config, stance_value=None):
    common_prefix = load_file("content/prompts/common_prefix.md")
    role_prompt = config.role_prompt       # 从 juror JSON 读取
    common_suffix = load_file("content/prompts/juror_suffix.md")
    current_stance = stance_value or self.stance_value

    return f"""{common_prefix}

## 你的角色
{role_prompt}

## 当前状态
- 你的有罪倾向值: {current_stance}/100
- 不要在对话中提及这个数值

{common_suffix}
"""
```

### B3.3 修改 `backend/agents/spoon_juror_agent.py` — JurorConfig 扩展

新增字段以支持新配置格式：

```python
@dataclass
class JurorConfig:
    id: str
    name: str
    codename: str               # 新增: 代号 (理中客/激进者...)
    role_prompt: str             # 新增: 角色专属 prompt
    weakness: dict               # 新增: { trigger_keywords, description }
    background: str
    personality: list[str]
    speaking_style: str
    initial_stance: int          # 现在是 0-100
    topic_weights: dict[str, int]
    first_message: str
    age: int = 0
    occupation: str = ""
    portrait: str = ""
```

### B3.4 修改 `backend/main.py` — 对话轮次限制

```python
@app.post("/chat/{juror_id}")
async def chat_with_juror(juror_id: str, request: ChatRequest, session_id: str):
    state = session_manager.get(session_id)
    require_phase(state, Phase.persuasion)

    rounds_used = state.juror_rounds_used.get(juror_id, 0)
    if rounds_used >= 10:
        raise HTTPException(429, detail="已用完与该陪审员的对话次数")

    response = await agent_manager.chat_with_juror(juror_id, request.message)
    state.juror_rounds_used[juror_id] = rounds_used + 1

    return {
        **response,
        "rounds_left": 10 - state.juror_rounds_used[juror_id]
    }
```

### B3.5 新增 API: `/juror/{id}/present/{evidence_id}` — 向陪审员出示证物

```
POST /juror/{juror_id}/present/{evidence_id}?session_id=xxx

→ { text, stance_delta, rounds_left }
```

将证物内容注入对话上下文，让陪审员 Agent 对证物做出反应。消耗1轮对话。

### B3.6 弱点触发检测

在 `spoon_juror_agent.py` 的 `chat()` 方法中，检测玩家消息是否包含弱点关键词：

```python
async def chat(self, player_message: str) -> dict:
    # 弱点检测
    weakness_triggered = False
    if self.juror_config.weakness:
        keywords = self.juror_config.weakness.get("trigger_keywords", [])
        if any(kw in player_message for kw in keywords):
            weakness_triggered = True
            # 额外 stance 偏移
            self.stance_value += WEAKNESS_IMPACT  # 向中间靠拢

    # ... 正常对话 ...

    return { ..., "weakness_triggered": weakness_triggered }
```

### B3.7 修改 `backend/services/agent_manager.py` — 适配新配置

`load_all_jurors()` 适配新的 JSON 格式和文件命名。

### 涉及文件

| 文件 | 操作 |
|------|------|
| `backend/agents/spoon_juror_agent.py` | 修改: 偏差值 + prompt + 弱点 + JurorConfig |
| `backend/main.py` | 修改: 轮次限制 + 出示证物API |
| `backend/services/agent_manager.py` | 修改: 适配新配置 |
| `backend/services/session_manager.py` | 修改: 轮次追踪 |

---

## 前端

### F3.1 修改陪审员列表 — 新卡片 UI

5个新陪审员，显示代号和身份：

```javascript
async function showJurorList() {
    const jurors = await getJurors();
    container.innerHTML = jurors.map(j => `
        <div class="juror-card" data-id="${j.id}" onclick="selectJuror('${j.id}')">
            <span class="juror-codename">${j.codename}</span>
            <span class="juror-name">${j.name}</span>
            <span class="juror-stance-hint">${j.stance_label || ''}</span>
        </div>
    `).join('');
}
```

### F3.2 对话轮次显示

在聊天区域顶部显示轮次计数器：

```html
<div class="chat-header">
    <span id="current-juror-name"></span>
    <span id="rounds-counter" class="rounds-badge">剩余: 10/10</span>
</div>
```

```javascript
function updateRoundsDisplay(roundsLeft) {
    const counter = document.getElementById('rounds-counter');
    counter.textContent = `剩余: ${roundsLeft}/10`;
    if (roundsLeft <= 3) counter.classList.add('low');
    if (roundsLeft === 0) counter.classList.add('exhausted');
}
```

### F3.3 轮次用尽处理

```javascript
async function handleSendMessage() {
    // ... 发送 ...

    const response = await chatWithJuror(gameState.currentJuror, message, gameState.sessionId);
    updateRoundsDisplay(response.rounds_left);

    if (response.rounds_left === 0) {
        disableChatInput();
        appendMessage('system', '你已用完与该陪审员的对话次数');
    }

    // 弱点触发视觉反馈
    if (response.weakness_triggered) {
        showWeaknessEffect();
    }
}
```

### F3.4 向陪审员出示证物

复用调查阶段的证物选择器，但调用不同 API：

```javascript
async function presentEvidenceToJuror(evidenceId) {
    const result = await request(
        `/juror/${gameState.currentJuror}/present/${evidenceId}?session_id=${gameState.sessionId}`,
        { method: 'POST' }
    );
    appendMessage('juror', result.text);
    updateRoundsDisplay(result.rounds_left);
}
```

### F3.5 弱点触发视觉反馈 (可选)

```javascript
function showWeaknessEffect() {
    const chatArea = document.getElementById('chat-messages');
    chatArea.classList.add('weakness-flash');
    setTimeout(() => chatArea.classList.remove('weakness-flash'), 1000);
}
```

```css
.weakness-flash {
    animation: flash-border 0.6s ease-in-out;
}
@keyframes flash-border {
    0%, 100% { border-color: transparent; }
    50% { border-color: var(--warning-color); }
}
```

### F3.6 修改 `api.js` — session_id 传递

所有陪审员相关 API 调用附加 `session_id` 参数。

### 涉及文件

| 文件 | 操作 |
|------|------|
| `frontend/js/game.js` | 修改: 陪审员列表 + 轮次 + 出示证物 |
| `frontend/js/api.js` | 修改: session_id 传递 |
| `frontend/index.html` | 修改: 轮次计数器 + 出示按钮 |
| `frontend/css/style.css` | 修改: 轮次样式 + 弱点动画 |

---

## 内容

| 文件 | 说明 |
|------|------|
| `content/jurors/j1_rationalist.json` | 理中客: stance=65, 弱点="政治操弄" |
| `content/jurors/j2_radical.json` | 激进者: stance=25, 弱点="主体性" |
| `content/jurors/j3_sympathizer.json` | 同情者: stance=30, 弱点="不需要同情" |
| `content/jurors/j4_opportunist.json` | 机奸: stance=35, 弱点="别惹事适得其反" |
| `content/jurors/j5_philosopher.json` | 哲学家: stance=50, 弱点="必须投票" |
| `content/prompts/common_prefix.md` | 通用 Agent 前缀 |
| `content/prompts/juror_suffix.md` | 陪审员后缀 (偏差值 + 对话规则) |

---

## 验收标准

- [ ] 显示5个新陪审员（带代号）
- [ ] 每个陪审员有独立性格、语气和立场
- [ ] 对话区顶部显示"剩余: X/10"
- [ ] 发送消息后轮次正确递减
- [ ] 10轮用完后输入框禁用，显示提示
- [ ] 可向陪审员出示证物，消耗1轮
- [ ] 触发弱点关键词时有视觉反馈
- [ ] 偏差值 >50 投有罪，≤50 投无罪
- [ ] 投票结果正确上链
