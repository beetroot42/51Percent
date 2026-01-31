# Phase 3 陪审员系统 Bug 修复任务 (Round 2)

> 生成时间: 2026-01-31
> 审查模型: Codex + Gemini 双模型交叉验证
> 上游任务: phase-3-bugfix.md (已完成)

---

## 问题概述

Codex 执行 Round 1 修复后，出现三个新 Bug：
1. 出示证物后 juror 无回话
2. 无法显示 juror 的回应
3. 投票卡在繁忙

---

## 根因分析

### Bug 1 & 2: Agent 循环逻辑缺陷 [Critical]

**文件**: `backend/agents/spoon_juror_agent.py`
**行号**: 341-377

```
当 LLM 返回 tool_calls + 文本回复时：
  → reply_text = "让我查看这个证物..."
  → tool_calls = [lookup_evidence]
  → 执行工具后 continue
  → reply_text 被丢弃
  → 循环结束后 final_reply = None
  → 返回 "Let me think a bit more about this case."
```

**问题**：
1. 工具调用后的 `continue` 导致文本回复被丢弃
2. 循环结束后的 fallback 是英文，与中文角色不符

### Bug 3: 投票工具同步阻塞 [Critical]

**文件**: `backend/tools/spoon_voting_tool.py`
**行号**: 125

```python
self._web3.eth.wait_for_transaction_receipt(tx_hash)  # 同步阻塞！
```

**问题**：
- `CastVoteTool.execute()` 声明为 `async def`
- 但内部调用同步阻塞方法 `wait_for_transaction_receipt()`
- 阻塞整个事件循环，导致前端显示"繁忙"

---

## 修复任务

### Task 1: 修复 Agent 循环逻辑 [Critical]

**文件**: `backend/agents/spoon_juror_agent.py`
**行号**: 337-401

```python
# 修改前 (简化)
async def chat(self, player_message: str) -> dict:
    tool_actions: list[dict] = []
    has_voted = False
    final_reply: str | None = None

    for _ in range(self.max_steps):
        response = await self._ask_with_tools()
        reply_text, tool_calls = self._extract_tool_calls(response)

        if tool_calls:
            if reply_text:
                await self.add_message("assistant", reply_text)
            # ... 执行工具 ...
            continue  # ⚠️ 丢弃 reply_text

        final_reply = reply_text or str(response)
        break

    if final_reply is None:
        final_reply = "Let me think a bit more about this case."  # ⚠️ 英文

# 修改后
async def chat(self, player_message: str) -> dict:
    tool_actions: list[dict] = []
    has_voted = False
    final_reply: str | None = None
    accumulated_text_parts: list[str] = []  # ✅ 新增：累积所有文本

    for _ in range(self.max_steps):
        response = await self._ask_with_tools()
        reply_text, tool_calls = self._extract_tool_calls(response)

        # ✅ 始终累积文本回复
        if reply_text:
            accumulated_text_parts.append(reply_text)

        if tool_calls:
            if reply_text:
                await self.add_message("assistant", reply_text)
            # ... 执行工具 ...
            continue

        final_reply = reply_text or str(response)
        break

    # ✅ 使用累积的文本作为 fallback
    if final_reply is None:
        if accumulated_text_parts:
            final_reply = "\n".join(accumulated_text_parts)
        else:
            final_reply = "让我再仔细想想这个案件。"  # ✅ 中文
```

---

### Task 2: 修复投票工具同步阻塞 [Critical]

**文件**: `backend/tools/spoon_voting_tool.py`
**行号**: 91-131

```python
# 在文件顶部添加 import
import asyncio

# 修改 execute 方法
async def execute(self, juror_index: int, guilty: bool) -> str:
    self._ensure_initialized()

    if juror_index < 0 or juror_index >= len(self.private_keys):
        raise ToolFailure(f"Juror index {juror_index} out of range")

    try:
        private_key = self.private_keys[juror_index]
        account = self._web3.eth.account.from_key(private_key)

        tx = self._contract.functions.vote(guilty).build_transaction({
            "from": account.address,
            "nonce": self._web3.eth.get_transaction_count(account.address),
            "gas": 200000,
            "gasPrice": self._web3.eth.gas_price,
            "chainId": self._web3.eth.chain_id,
        })

        signed_tx = self._web3.eth.account.sign_transaction(tx, private_key)
        raw_tx = getattr(signed_tx, "rawTransaction", None) or signed_tx.raw_transaction
        tx_hash = self._web3.eth.send_raw_transaction(raw_tx)

        # ✅ 修复：使用 asyncio.to_thread 将同步阻塞移到线程池
        await asyncio.to_thread(
            self._web3.eth.wait_for_transaction_receipt, tx_hash
        )

        vote_type = "GUILTY" if guilty else "NOT_GUILTY"
        return f"Vote cast successfully: {vote_type}, tx_hash: {tx_hash.hex()}"

    except Exception as e:
        raise ToolFailure(f"Vote cast failed: {str(e)}", cause=e)
```

---

### Task 3: 前端空值保护 [Major]

**文件**: `frontend/js/game.js`
**函数**: `appendMessage` (行号 1547-1574)

```javascript
// 修改前
function appendMessage(role, text) {
    const container = document.getElementById('chat-messages');
    if (!container) return;
    // ...
    msgDiv.querySelector('.text').textContent = text;
}

// 修改后
function appendMessage(role, text) {
    const container = document.getElementById('chat-messages');
    if (!container) {
        console.error('[appendMessage] Chat container not found');
        return null;
    }

    // ✅ 空值保护
    const displayText = text ?? '（无回应）';
    if (!text) {
        console.warn('[appendMessage] Empty text for role:', role);
    }

    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role} fade-in`;

    const speakerName = role === 'player'
        ? 'OVERSEER'
        : (role === 'system' ? 'SYSTEM' : (document.getElementById('current-juror-name')?.textContent || 'JUROR'));

    msgDiv.innerHTML = `
        <div class="speaker">${speakerName}</div>
        <div class="text"></div>
    `;

    container.appendChild(msgDiv);
    msgDiv.querySelector('.text').textContent = displayText;  // ✅ 使用 displayText
    container.scrollTop = container.scrollHeight;

    return msgDiv;
}
```

---

### Task 4: 前端证物响应兼容 [Major]

**文件**: `frontend/js/game.js`
**函数**: `handleShowEvidence` (行号 1267-1270)

```javascript
// 修改前
appendMessage('juror', response.text);
gameState.chatHistory[gameState.currentJuror].push({ role: 'juror', content: response.text });

// 修改后
const replyText = response.text || response.reply || '（陪审员正在思考...）';
appendMessage('juror', replyText);
gameState.chatHistory[gameState.currentJuror].push({ role: 'juror', content: replyText });
```

---

### Task 5: 投票进度条优化 [Minor]

**文件**: `frontend/js/game.js`
**函数**: `handleVotingProcess` (行号 608-686)

**问题**: 进度条动画固定时间，与实际投票时间不同步

**修复方案**: 使用持续动画替代固定时间动画

```javascript
// 在 步骤3 部分修改
steps[1]?.classList.remove('active');
steps[2]?.classList.add('active');
statusText.textContent = '等待本地区块链确认...';

// ✅ 使用持续动画
const animationInterval = setInterval(() => {
    const current = parseFloat(progressBar.style.width) || 60;
    if (current < 95) {
        progressBar.style.width = `${Math.min(current + 0.3, 95)}%`;
    }
}, 300);

try {
    const result = await votePromise;
    clearInterval(animationInterval);
    clearTimeout(busyHintTimer);
    // ... 成功处理
} finally {
    clearInterval(animationInterval);
}
```

---

## 验收标准

- [ ] 出示证物后陪审员正常回复（中文）
- [ ] 发送消息后陪审员正常回复
- [ ] 投票流程不再卡住，进度条持续更新
- [ ] 空回复时显示友好提示而非空白
- [ ] 控制台无 JS 错误

---

## 文件变更清单

| 文件 | 操作 | 优先级 |
|------|------|--------|
| `backend/agents/spoon_juror_agent.py` | 修改 chat() 循环逻辑 | Critical |
| `backend/tools/spoon_voting_tool.py` | 添加 asyncio.to_thread | Critical |
| `frontend/js/game.js` | 修改 appendMessage 空值保护 | Major |
| `frontend/js/game.js` | 修改 handleShowEvidence 兼容 | Major |
| `frontend/js/game.js` | 修改 handleVotingProcess 动画 | Minor |

---

## 审查评分

| 评分项 | Codex (后端) | Gemini (前端) |
|--------|-------------|---------------|
| 根因定位 | 18/20 | 12/20 |
| 代码质量 | 17/20 | 15/20 |
| 交叉验证 | 一致 | 一致 |
| 总分 | 87/100 | 75/100 |

**结论**: 根因已定位，修复方案明确
