# Phase 4: 结局系统

## 目标

投票完成 → 判决展示 → 结局文本 → Blake 反应 (可选)

---

## 后端

### B4.1 新增 API: `/story/ending`

```
GET /story/ending?session_id=xxx

→ {
    type: "guilty" | "not_guilty" | "betrayal",
    text: str,
    blake_reaction: str | null
  }
```

结局判定逻辑：

```python
@app.get("/story/ending")
async def get_ending(session_id: str):
    state = session_manager.get(session_id)

    # 统计投票
    guilty_count = sum(
        1 for s in state.juror_stance.values() if s > 50
    )

    # 判定结局类型
    if guilty_count >= 3:
        ending_type = "guilty"
    else:
        ending_type = "not_guilty"

    # TODO: 背叛结局条件（后续设计文档补充）
    # 可能的判定：玩家引导了无罪，但任务是有罪
    # if guilty_count < 3 and player_was_assigned_guilty:
    #     ending_type = "betrayal"

    ending = load_json(f"content/story/ending_{ending_type}.json")
    return {
        "type": ending_type,
        "text": ending.get("text", ""),
        "blake_reaction": ending.get("blake_reaction", None)
    }
```

### B4.2 修改 `/vote` — 关联 session

投票端点增加 session_id，从 SessionState 中读取 juror stance 判定投票。

### B4.3 修改 `/reset` — 清理会话

重置游戏时清理 session state，phase 回到 prologue。

### 涉及文件

| 文件 | 操作 |
|------|------|
| `backend/main.py` | 修改: 新增 ending API + 修改 vote/reset |

---

## 前端

### F4.1 结局展示页面

投票完成后，调用 `/story/ending` 获取结局并展示：

```javascript
async function showEnding() {
    const ending = await request(`/story/ending?session_id=${gameState.sessionId}`);

    const container = document.getElementById('ending-container');
    container.className = `ending ending-${ending.type}`;

    // 判决标题
    const titles = {
        guilty: '有罪',
        not_guilty: '无罪',
        betrayal: '背叛'
    };

    container.innerHTML = `
        <div class="ending-header">
            <h1 class="ending-title">${titles[ending.type]}</h1>
        </div>
        <div class="ending-text">
            <p>${ending.text}</p>
        </div>
        ${ending.blake_reaction ? `
            <div class="blake-reaction">
                <div class="npc-portrait blake small"></div>
                <p>${ending.blake_reaction}</p>
            </div>
        ` : ''}
    `;

    container.classList.remove('hidden');
}
```

### F4.2 结局视觉风格

三种结局使用不同配色：

```css
.ending-guilty {
    --ending-color: #e94560;
    background: linear-gradient(135deg, #1a1a2e, #3a0015);
    border-color: var(--ending-color);
}

.ending-not_guilty {
    --ending-color: #0f9b58;
    background: linear-gradient(135deg, #1a1a2e, #003a15);
    border-color: var(--ending-color);
}

.ending-betrayal {
    --ending-color: #f0a030;
    background: linear-gradient(135deg, #1a1a2e, #3a2a00);
    border-color: var(--ending-color);
}

.ending-title {
    color: var(--ending-color);
    font-size: 3rem;
    text-align: center;
    text-shadow: 0 0 20px var(--ending-color);
    animation: glow-pulse 2s ease-in-out infinite;
}

@keyframes glow-pulse {
    0%, 100% { text-shadow: 0 0 20px var(--ending-color); }
    50% { text-shadow: 0 0 40px var(--ending-color), 0 0 80px var(--ending-color); }
}

.blake-reaction {
    margin-top: 2rem;
    padding: 1rem;
    border-left: 3px solid var(--accent-color);
    display: flex;
    align-items: flex-start;
    gap: 1rem;
}
```

### F4.3 修改投票流程 — 链接结局

修改 `enterVerdict()` 流程：

```javascript
async function enterVerdict() {
    // ... 现有投票流程 ...

    // 投票完成后，显示结局
    await showVotingAnimation(result);
    showVerdict(result.verdict);

    // 新增: 获取并显示结局文本
    await showEnding();

    // 保留: 链上验证
    await showVerificationPanel();
}
```

### F4.4 修改 `index.html` — 结局容器

```html
<!-- 在 verdict-phase section 内新增 -->
<div id="ending-container" class="ending hidden"></div>
```

### 涉及文件

| 文件 | 操作 |
|------|------|
| `frontend/js/game.js` | 修改: 结局展示 + 投票流程链接 |
| `frontend/index.html` | 修改: 结局容器 |
| `frontend/css/style.css` | 修改: 结局样式 |

---

## 内容

| 文件 | 说明 |
|------|------|
| `content/story/ending_guilty.json` | 有罪结局文本 + Blake 反应 |
| `content/story/ending_not_guilty.json` | 无罪结局文本 + Blake 反应 |
| `content/story/ending_betrayal.json` | 背叛结局文本 + Blake 反应 |

JSON 格式：
```json
{
  "type": "guilty",
  "text": "[占位：有罪结局叙事文本]",
  "blake_reaction": "[占位：Blake 对结果的反应]"
}
```

---

## 验收标准

- [ ] 投票完成后显示结局文本
- [ ] 有罪结局使用红色调
- [ ] 无罪结局使用绿色调
- [ ] 背叛结局使用橙色调（如果实现）
- [ ] 结局文本与判决结果匹配
- [ ] Blake 反应文本正确显示（如果有）
- [ ] 链上验证面板仍然正常显示
- [ ] 重新开始按钮回到 prologue 阶段
