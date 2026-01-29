# 任务：修复 ReAct Agent 测试

## 背景
新创建的两个测试文件存在 Mock 兼容性问题，导致 6 个测试失败。

## 问题诊断
**根因**：`SpoonJurorAgent` 使用 `pydantic.Field(default=...)` 定义 `max_steps` 和 `tool_choices`，但测试中的 Mock `ToolCallAgent` 是普通 Python 类，不会处理 Pydantic Field 定义，导致这些属性保持为 `FieldInfo` 对象而非具体值。

**错误信息**：
```
TypeError: 'FieldInfo' object cannot be interpreted as an integer
```

## 任务清单

### 1. 修复 test_react_agent.py 的 Mock
**文件**：`backend/tests/test_react_agent.py`

在 `_install_spoon_ai_stubs` 函数中的 `ToolCallAgent` 类的 `__init__` 方法末尾添加 Field 默认值提取逻辑：

```python
class ToolCallAgent:
    def __init__(self, name, description, system_prompt, llm, memory, available_tools, **kwargs):
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.llm = llm
        self.memory = memory
        self.available_tools = available_tools
        self.state = AgentState.IDLE
        self.current_step = 0

        # Mock Pydantic Field handling - 提取子类 Field 默认值
        for key in dir(self):
            if key in ["max_steps", "tool_choices"]:
                val = getattr(self.__class__, key, None)
                if val and hasattr(val, "default"):
                    setattr(self, key, val.default)

    async def add_message(self, role, content):
        self.memory.messages.append({"role": role, "content": content})
```

### 2. 同步修复 test_evidence_tool.py（可选）
**文件**：`backend/tests/test_evidence_tool.py`

如果 `BaseTool` Mock 也有类似问题，添加相同的 Field 处理逻辑。

### 3. 运行测试验证
```bash
cd D:/51-DEMO/ai-trial-game/backend
python -m pytest tests/test_evidence_tool.py tests/test_react_agent.py -v
```

**预期结果**：27 passed

## 验收标准
- [ ] 所有测试通过 (27 passed)
- [ ] 无新增 warning
- [ ] 不修改生产代码（仅修改测试文件）

## 相关文件
- `backend/tests/test_react_agent.py` - 主要修复目标
- `backend/tests/test_evidence_tool.py` - 检查是否需要同步修复
- `backend/tests/test_spoon_juror_agent.py` - 参考现有 Mock 模式
