# Task: Frontend Updates (Gemini)

**Phase**: 2 - Frontend Updates
**Assigned to**: Gemini
**Priority**: High
**Specification**: `local-chain-migration-spec.md`

---

## 🎯 Objective

Update frontend to support Anvil local chain by:
1. Removing Etherscan external links
2. Updating network terminology
3. Reducing animation duration for instant confirmations
4. Adding infrastructure error detection

---

## 📋 Implementation Tasks

### Task 2.1: Remove Etherscan Links
**File**: `frontend/js/game.js`

**Location**: Around line 123 in `enterVerdict()` function

**Current Code**:
```javascript
const etherscanUrl = `https://sepolia.etherscan.io/tx/${hash}`;
// Creates clickable link to Sepolia Etherscan
```

**Required Change**:
```javascript
// Remove Etherscan URL construction
// Display transaction hash as plain text (copyable)

verdictElement.innerHTML = `
    <div class="verdict-result">
        <h3>判决结果</h3>
        <p class="verdict-text">${verdict === 'Not Guilty' ? '✓ 无罪' : '✗ 有罪'}</p>
        <div class="tx-info">
            <p>交易哈希:</p>
            <code class="tx-hash">${hash}</code>
        </div>
        <p class="finality-note">判决已记录在本地区块链，不可篡改</p>
    </div>
`;
```

**CSS Addition** (optional styling in `frontend/css/style.css`):
```css
.tx-hash {
    display: block;
    background: #f5f5f5;
    padding: 8px;
    border-radius: 4px;
    font-size: 12px;
    word-break: break-all;
    user-select: all; /* Allow easy copying */
    margin: 8px 0;
}

.finality-note {
    font-size: 14px;
    color: #666;
    font-style: italic;
}
```

**CONSTRAINT**: Do NOT link to any external block explorer.

---

### Task 2.2: Update Network Terminology
**File**: `frontend/index.html`

**Location**: Around line 148 (verdict phase section)

**Current Text**:
```html
<li>2. 提交区块链 (Sepolia)</li>
```

**Required Change**:
```html
<li>2. 提交区块链 (本地链)</li>
```

**Additional locations to check**:
- Search for all instances of "Sepolia" in `index.html`
- Replace with "本地链" or "Anvil" as appropriate

**Example search-replace**:
```bash
# Search pattern: "Sepolia"
# Replace with: "本地链"
```

---

### Task 2.3: Reduce Animation Duration
**File**: `frontend/js/game.js`

**Location**: Around line 167 in `handleVotingProcess()` function

**Current Code**:
```javascript
// Step 3: Wait for block confirmation (~9 seconds for Sepolia)
animateProgressBar(60, 90, 9000);
```

**Required Change**:
```javascript
// Step 3: Wait for block confirmation (~2 seconds for local chain)
animateProgressBar(60, 90, 2000);  // Changed from 9000 to 2000
```

**Rationale**: Anvil confirms transactions instantly (<1s), so 2s provides smooth visual feedback without feeling sluggish.

**INVARIANT**: Total voting animation should complete in ~4-5 seconds (down from ~15s).

---

### Task 2.4: Enhanced Error Handling
**File**: `frontend/js/game.js`

**Location**: Around line 115 in `handleVoting()` or similar error catch block

**Current Code**:
```javascript
catch (error) {
    showError(`投票失败: ${error.message}`);
}
```

**Required Change**:
```javascript
catch (error) {
    console.error("Voting error:", error);

    // Distinguish infrastructure vs logic errors
    if (error.message.includes("ECONNREFUSED") ||
        error.message.includes("fetch failed") ||
        error.message.includes("Failed to fetch")) {
        showError(
            "⚠️ 本地链连接失败\n\n" +
            "请检查:\n" +
            "1. Anvil 进程是否正在运行\n" +
            "2. 后端服务是否启动\n" +
            "3. 查看终端日志获取详细信息"
        );
    } else if (error.message.includes("already voted") ||
               error.message.includes("not a juror")) {
        showError(`投票被拒绝: ${error.message}`);
    } else {
        showError(`投票失败: ${error.message}`);
    }
}
```

**Rationale**: Helps users distinguish between:
- **Infrastructure errors**: Anvil not running, network issues
- **Logic errors**: Contract validation failures (already voted, not whitelisted)
- **Other errors**: Unexpected issues

---

### Task 2.5: Update Voting Progress Text
**File**: `frontend/js/game.js`

**Location**: Around line 160-170 in `handleVotingProcess()` function

**Current Progress Messages**:
```javascript
updateProgressMessage("正在连接 Sepolia 测试网...");
updateProgressMessage("等待区块确认...");
```

**Required Changes**:
```javascript
// Step 1
updateProgressMessage("正在连接本地区块链...");

// Step 2
updateProgressMessage("正在提交投票交易...");

// Step 3
updateProgressMessage("等待区块确认...");  // Keep this (generic)

// Step 4
updateProgressMessage("投票完成！");
```

---

## ✅ Acceptance Criteria

After implementation, verify:

1. **No Etherscan links**:
   - Verdict display shows transaction hash as plain text
   - No clickable links to external explorers
   - Hash is copyable (user-select: all)

2. **Network terminology**:
   - All references to "Sepolia" changed to "本地链"
   - UI text reflects local environment

3. **Animation speed**:
   - Voting process completes in ~4-5 seconds total
   - Step 3 animation is 2 seconds (not 9)

4. **Error messages**:
   - Anvil connection errors show specific guidance
   - Logic errors (contract rejections) clearly distinguished
   - Helpful troubleshooting tips included

5. **Visual polish**:
   - Transaction hash is readable and styled
   - Progress messages are clear and accurate
   - No broken UI elements

---

## 🎨 UI/UX Improvements (Optional)

If time permits, consider these enhancements:

### 1. Local Mode Indicator
**File**: `frontend/index.html`

Add a badge to indicate local mode:
```html
<div class="network-badge">
    <span class="status-dot"></span>
    本地链模式
</div>
```

### 2. Transaction Hash Copy Button
**File**: `frontend/js/game.js`

Add a "Copy" button next to the hash:
```javascript
<button onclick="copyToClipboard('${hash}')" class="copy-btn">复制</button>

function copyToClipboard(text) {
    navigator.clipboard.writeText(text);
    showNotification("交易哈希已复制");
}
```

### 3. Real-time Connection Status
**File**: `frontend/js/api.js`

Add a heartbeat check for backend/Anvil:
```javascript
async function checkConnection() {
    try {
        await fetch('/state');
        return true;
    } catch {
        return false;
    }
}
```

**Note**: These are optional enhancements, not required for MVP.

---

## 🚫 Critical Constraints

1. **Do NOT modify backend code** - Only frontend files
2. **Do NOT remove error handling** - Enhance it, don't simplify
3. **Preserve game logic** - Only change presentation layer
4. **Test all UI states** - Ensure no broken elements

---

## 📂 Files to Modify

| File | Changes | Priority |
|------|---------|----------|
| `frontend/js/game.js` | ~30 lines modified | Critical |
| `frontend/index.html` | ~5 lines modified | High |
| `frontend/css/style.css` | +15 lines (optional styling) | Medium |

**Do NOT modify**:
- `frontend/js/api.js` (unless adding optional features)
- Backend files
- Contract files

---

## 🧪 Testing Checklist

After implementation, manually test:

- [ ] Start game in local mode
- [ ] Complete full conversation flow
- [ ] Trigger voting
- [ ] Verify no Etherscan links appear
- [ ] Verify animation completes in ~4-5s
- [ ] Stop Anvil mid-game and verify error message
- [ ] Copy transaction hash successfully
- [ ] Check all text says "本地链" not "Sepolia"

---

## 📖 Reference

**Specification Sections**: FR-6.1, FR-6.2, FR-6.3
**Related Files**:
- Analysis: `.claude/tasks/architecture-analysis-local-chain.md`
- Full Spec: `.claude/tasks/local-chain-migration-spec.md`

---

**Ready for Implementation**: ✅
**Estimated Time**: 1-2 hours
**Dependencies**: None (can run parallel with backend work)
