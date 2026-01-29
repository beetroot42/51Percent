[根目录](../CLAUDE.md) > **frontend**

# Frontend 模块

> 纯静态 HTML/CSS/JS 游戏界面

## 变更记录 (Changelog)

| 时间 | 操作 | 说明 |
|------|------|------|
| 2026-01-28 12:33:00 | 更新 | 添加 Playwright E2E 测试 |
| 2026-01-28 11:54:54 | 创建 | 初始化模块文档 |

---

## 模块职责

- 提供三阶段游戏界面 (调查/说服/审判)
- 与后端 API 交互
- 显示链上投票结果和验证信息
- 提供本地区块浏览器

---

## 入口与启动

前端由后端 FastAPI 静态托管:

```bash
cd backend
python main.py
# 访问 http://localhost:5000/game
```

或直接打开 `index.html` (需后端运行)。

---

## 对外接口

### API 调用 (api.js)

| 函数 | 端点 | 说明 |
|------|------|------|
| `getGameState()` | GET /state | 获取状态 |
| `setPhase(phase)` | POST /phase/{phase} | 切换阶段 |
| `getJurors()` | GET /jurors | 陪审员列表 |
| `chatWithJuror(id, msg)` | POST /chat/{id} | 对话 |
| `triggerVote()` | POST /vote | 投票 |
| `getDossier()` | GET /content/dossier | 卷宗 |

---

## 关键依赖与配置

**无外部依赖** - 纯原生 JavaScript (ES6+)

### 文件结构

```
frontend/
+-- index.html          # 主游戏页面
+-- block-explorer.html # 本地区块浏览器
+-- css/
|   +-- style.css       # 游戏样式
|   +-- explorer.css    # 浏览器样式
+-- js/
    +-- api.js          # API 调用封装
    +-- game.js         # 游戏主逻辑
    +-- dialogue.js     # 证人对话系统
```

---

## 数据模型

### gameState (game.js)

```javascript
const gameState = {
    phase: 'investigation',  // investigation | persuasion | verdict
    currentJuror: null,      // 当前对话的陪审员 ID
    chatHistory: {},         // {juror_id: [{role, content}, ...]}
    evidenceList: [],        // 证据列表缓存
};
```

### 游戏阶段

1. **investigation** - 调查阶段
   - 卷宗面板 (dossier-panel)
   - 证据面板 (evidence-panel)
   - 证人面板 (witnesses-panel)

2. **persuasion** - 说服阶段
   - 陪审员列表 (juror-list)
   - 对话区域 (chat-area)

3. **verdict** - 审判阶段
   - 投票动画 (voting-animation)
   - 投票统计 (vote-stats)
   - 判决结果 (verdict-result)
   - 链上验证 (verification-panel)

---

## 测试与质量

### E2E 测试 (Playwright)

测试文件位于 `tests/e2e/`:

```bash
# 安装依赖
npm install -D @playwright/test
npx playwright install chromium

# 运行测试 (需后端运行在 localhost:5000)
npx playwright test --config=tests/e2e/playwright.config.js
```

| 测试文件 | 覆盖场景 |
|----------|----------|
| `game-flow.spec.js` | 完整游戏流程 (调查→说服→审判→验证) |
| `investigation.spec.js` | 卷宗/证据/当事人对话 |
| `persuasion.spec.js` | 陪审员选择/对话/历史保持 |
| `verdict.spec.js` | 投票流程/判决显示/链上验证 |

测试使用 API Mock (page.route) 模拟后端响应，可独立运行。

### 手动测试流程

1. 启动后端和 Anvil
2. 访问 `/game`
3. 完成调查阶段
4. 与陪审员对话
5. 触发投票
6. 验证链上结果

---

## 常见问题 (FAQ)

**Q: 页面无法加载?**
A: 确保后端运行在 5000 端口。

**Q: 对话无响应?**
A: 检查后端日志，可能是 LLM API 错误。

**Q: 投票超时?**
A: 确保 Anvil 正常运行，检查 RPC 连接。

**Q: 如何查看交易详情?**
A: 点击"查看区块详情"打开 block-explorer.html。

---

## 相关文件清单

| 文件 | 行数 | 说明 |
|------|------|------|
| `index.html` | 277 | 主游戏页面 |
| `block-explorer.html` | - | 本地区块浏览器 |
| `js/game.js` | 904 | 游戏主逻辑 |
| `js/api.js` | 107 | API 调用封装 |
| `js/dialogue.js` | - | 证人对话系统 |
| `css/style.css` | - | 游戏样式 |
