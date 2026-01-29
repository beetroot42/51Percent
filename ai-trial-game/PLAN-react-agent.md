# 计划：ai-trial-game 升级为 ReAct Agent

## 目标

将 SpoonJurorAgent 从"对话型 Agent"升级为真正的 ReAct Agent，启用工具调用循环（Reason → Tool → Act），增加 2 个工具：

1. **证据检索工具** (EvidenceLookupTool) — 只读，Agent 主动查阅案件证据
2. **链上投票工具** (CastVoteTool) — 写操作，Agent 在对话中自主决定投票并上链

## 约束

- 保持游戏核心玩法不变（玩家说服 → 陪审员投票）
- 工具调用过程以**叙事方式**展示（融入角色语言）
- Agent 在对话中自主决定何时投票（不再由系统统一触发）
- 代码改动尽量小（目标 < 150 行新增/修改）

---

## Step 1：新建证据检索工具

**文件**: `backend/tools/evidence_tool.py` (新建)

```python
class EvidenceLookupTool(BaseTool):
    name = "lookup_evidence"
    description = "查阅案件证据详情。可用证据: chat_history(聊天记录), log_injection(注入日志), safety_report(安全报告), dossier(案件卷宗)"
    parameters = {
        "type": "object",
        "properties": {
            "evidence_id": {
                "type": "string",
                "enum": ["chat_history", "log_injection", "safety_report", "dossier"],
                "description": "要查阅的证据ID"
            }
        },
        "required": ["evidence_id"]
    }
```

- 从 `content/case/evidence/*.json` 和 `content/case/dossier.json` 读取
- 返回证据的 `content` 字段文本
- 继承 `spoon_ai.tools.base.BaseTool`

---

## Step 2：修改 SpoonJurorAgent 启用工具

**文件**: `backend/agents/spoon_juror_agent.py` (修改)

### 2a. 启用工具调用

```python
# 改前
tool_choices: Any = Field(default=ToolChoice.NONE)
max_steps: int = Field(default=1)

# 改后
tool_choices: Any = Field(default=ToolChoice.AUTO)
max_steps: int = Field(default=3)  # 最多 3 步推理
```

### 2b. 注入工具到 ToolManager

```python
# 改前
available_tools=ToolManager([])

# 改后
from tools.evidence_tool import EvidenceLookupTool
from tools.spoon_voting_tool import CastVoteTool

tools_list = [EvidenceLookupTool(content_path=content_path)]
# 如果有投票配置，也注入 CastVoteTool
if voting_config:
    tools_list.append(CastVoteTool(**voting_config))

available_tools=ToolManager(tools_list)
```

### 2c. 重写 chat() 支持工具循环

修改 `chat()` 方法，使用 ToolCallAgent 的标准工具循环：
- LLM 返回时检查是否包含 tool_calls
- 如果有，执行工具并将结果反馈给 LLM
- 收集工具调用记录，返回给前端（叙事化）

返回格式变更：
```python
return {
    "reply": clean_reply,
    "juror_id": self.juror_id,
    "stance_label": self._get_stance_label(),
    "tool_actions": [  # 新增
        {"tool": "lookup_evidence", "input": "safety_report", "narrative": "让我看看那份安全报告..."},
        {"tool": "cast_vote", "input": {"guilty": False}, "narrative": "我已经做出了决定，投下无罪票。", "tx_hash": "0x..."}
    ],
    "has_voted": False  # 新增：是否已投票
}
```

### 2d. 删除 think()/act() 的空实现

删除当前的禁用覆盖，让 ToolCallAgent 基类的工具循环生效。

### 2e. 更新系统提示词

在 `_build_roleplay_prompt()` 中增加工具使用指引：

```
## 可用工具
你可以使用以下工具来辅助你的判断：
- lookup_evidence: 查阅案件证据（聊天记录、注入日志、安全报告、案件卷宗）
- cast_vote: 当你做出最终决定时，直接在区块链上投票

## 工具使用规则
1. 当玩家提到某个证据或你需要核实事实时，主动调用 lookup_evidence
2. 只在你真正下定决心后才调用 cast_vote（一旦投票不可更改）
3. 不要每次回复都查证据，只在有需要时查
4. 投票前要有充分的推理过程
```

---

## Step 3：修改 API 返回格式

**文件**: `backend/main.py` (修改)

ChatResponse 模型增加可选字段：

```python
class ChatResponse(BaseModel):
    reply: str
    juror_id: str
    tool_actions: list[dict] = []  # 新增
    has_voted: bool = False         # 新增
```

---

## Step 4：前端叙事化展示

**文件**: `frontend/js/dialogue.js` (修改)

处理 `tool_actions` 字段：
- 在陪审员回复前，逐条展示叙事化的工具调用
- 证据检索：展示为斜体/引用样式，如 *「让我看看那份安全报告...」*
- 投票：展示为高亮事件，如 **陪审员王大爷已投票：无罪 (tx: 0xabc...)**

---

## Step 5：投票配置传递

**文件**: `backend/services/agent_manager.py` (修改)

AgentManager 初始化时，将投票工具配置传给每个 SpoonJurorAgent：

```python
def load_all_jurors(self, content_path, voting_config=None):
    for juror_id in self.juror_ids:
        self.agents[juror_id] = SpoonJurorAgent(
            juror_id=juror_id,
            content_path=str(content_dir),
            voting_config=voting_config  # 新增
        )
```

---

## 影响范围

| 文件 | 操作 | 改动量 |
|------|------|--------|
| `backend/tools/evidence_tool.py` | 新建 | ~50 行 |
| `backend/agents/spoon_juror_agent.py` | 修改 | ~60 行 |
| `backend/main.py` | 修改 | ~10 行 |
| `backend/services/agent_manager.py` | 修改 | ~10 行 |
| `frontend/js/dialogue.js` | 修改 | ~30 行 |

**总计**: ~160 行，5 个文件

## ReAct 循环示例

```
玩家: "你看过安全报告吗？那个机器人是通过了认证的！"

Agent 内部:
  [Thought] 玩家提到了安全报告，我应该查一下
  [Action] lookup_evidence("safety_report")
  [Observation] "ARIA-7通过了ISO 15066安全认证..."
  [Thought] 认证确实存在，但这不能说明它无罪...

前端展示:
  陪审员: *翻阅了安全报告...*
  陪审员: "认证是通过了，但认证只覆盖已知风险。新型攻击总是走在防御前面。"
```
