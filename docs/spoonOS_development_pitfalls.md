# SpoonOS DM Agent Development Pitfalls Summary

**Date**: 2026-01-26  
**Project**: DM Agent (D&D 5e Character Creation Assistant)  
**Collaboration Mode**: Antigravity (Gemini) + Codex (Claude)

---

## 🎯 Project Goal

Create a TRPG Dungeon Master Agent based on SpoonOS, using third-party OpenAI-compatible API to relay to Claude, implementing D&D 5e character creation flow.

---

## 🐛 Problems Encountered and Solutions

### 1. ✅ Gemini Model Configuration Error Causing 503

**Problem Description**:
```
503 UNAVAILABLE. The model is overloaded. Please try again later.
```

**Root Cause**:  
[dm_agent_demo.py](file:///D:/react%20Agent/spoon-core/examples/dm_agent/dm_agent_demo.py) used `gemini-3-flash-preview` model, which doesn't exist or is extremely unstable.

**Solution**:  
Changed to stable model name:
```python
# Wrong ❌
model_name="gemini-3-flash-preview"

# Correct ✅
model_name="gemini-1.5-flash"
```

**Lesson**: 
- Use officially documented stable model names
- When encountering 503, first check if model name is correct

---

### 2. ✅ OpenAI Compatible Provider Not Registered

**Problem Description**:
```
ConfigurationError: Provider 'openai_compatible' not registered
```

**Root Cause**:  
[OpenAICompatibleProvider](file:///D:/react%20Agent/spoon-core/spoon_ai/llm/providers/openai_compatible_provider.py#33-990) class exists as base class but wasn't registered to global registry using `@register_provider` decorator.

**Solution**:  
Add decorator in [spoon_ai/llm/providers/openai_compatible_provider.py](file:///D:/react%20Agent/spoon-core/spoon_ai/llm/providers/openai_compatible_provider.py):

```python
from ..registry import register_provider
from ..interface import ProviderCapability

@register_provider("openai_compatible", [
    ProviderCapability.CHAT,
    ProviderCapability.COMPLETION,
    ProviderCapability.TOOLS,
    ProviderCapability.STREAMING
])
class OpenAICompatibleProvider(LLMProviderInterface):
    ...
```

**Lessons**:
- SpoonOS Providers must be explicitly registered to be used
- Base classes don't auto-register, even if subclasses are registered
- Use [get_global_registry().list_providers()](file:///D:/react%20Agent/spoon-core/spoon_ai/llm/registry.py#217-224) to verify registration status

---

### 3. ✅ Base URL Duplicate Concatenation Causing 404

**Problem Description**:
```
404 - Invalid URL (POST /v1/chat/completions/chat/completions)
```

**Root Cause**:  
User configured in [.env](file:///D:/react%20Agent/spoon-core/.env):
```bash
OPENAI_COMPATIBLE_BASE_URL=https://ai.huan666.de/v1/chat/completions
```

OpenAI SDK automatically appends `/chat/completions`, causing URL to become:
```
https://ai.huan666.de/v1/chat/completions/chat/completions
```

**Solution**:  
Clean URL in [openai_compatible_provider.py](file:///D:/react%20Agent/spoon-core/spoon_ai/llm/providers/openai_compatible_provider.py) [initialize](file:///D:/react%20Agent/spoon-core/spoon_ai/llm/providers/openai_compatible_provider.py#126-179) method:

```python
async def initialize(self, config: Dict[str, Any]) -> None:
    base_url = config.get('base_url') or self.get_default_base_url()
    
    # Clean base_url, remove possible /chat/completions suffix
    if base_url and base_url.endswith('/chat/completions'):
        base_url = base_url.rsplit('/chat/completions', 1)[0]
        logger.info(f"Cleaned base_url to: {base_url}")
    
    self.client = AsyncOpenAI(
        api_key=api_key,
        base_url=base_url,
        ...
    )
```

**Lessons**:
- **Correct Base URL Configuration**: Should only go to `/v1`, not include `/chat/completions`
  ```bash
  # Correct ✅
  OPENAI_COMPATIBLE_BASE_URL=https://ai.huan666.de/v1
  
  # Wrong ❌
  OPENAI_COMPATIBLE_BASE_URL=https://ai.huan666.de/v1/chat/completions
  ```
- Framework layer should have fault tolerance for common configuration errors
- Logs should explicitly indicate URL cleaning operations

---

### 4. ✅ Virtual Environment Issues

**Problem Description**:
```
ModuleNotFoundError: No module named 'spoon_ai'
```

**Root Cause**:  
Using system Python ([py](file:///D:/react%20Agent/spoon-core/spoon_ai/llm/manager.py)) instead of virtual environment Python.

**Solution**:  
Must use virtual environment:
```bash
# Wrong ❌
py examples/dm_agent/dm_agent_demo.py

# Correct ✅
.\spoon-env\Scripts\python.exe examples/dm_agent/dm_agent_demo.py
```

**Lessons**:
- SpoonOS is installed with `-e .`, only available in virtual environment
- Documentation and README should clearly emphasize virtual environment usage
- Can add environment check at script start

---

### 5. ✅ Batch Dice Rolling Feature Implementation

**Requirement**: Generate all six main attributes at once, instead of asking one by one.

**Implementation Points**:

**[tools/dice_roller.py](file:///D:/react%20Agent/spoon-core/examples/dm_agent/tools/dice_roller.py) Modification**:
```python
async def execute(self, stat_name: str) -> str:
    if stat_name.lower() == "all":
        stat_order = ["Strength", "Dexterity", "Constitution", 
                      "Intelligence", "Wisdom", "Charisma"]
        output = {
            "stats": {name: self._roll_stat(name) for name in stat_order},
            "stat_order": stat_order
        }
        return json.dumps(output, ensure_ascii=False, indent=2)
    
    # Single attribute rolling...
```

**System Prompt Update**:
```python
system_prompt: str = """...
4. **Batch roll attributes**: Use roll_stat tool to generate all six attributes at once
...
## Tool Usage Examples:
- roll_stat: Use when need to generate all six attributes at once, pass {"stat_name": "all"}
"""
```

**Lessons**:
- Agent's prompt must sync with tool capabilities
- Use special parameter values (like `"all"`) for batch operations
- Maintain backward compatibility (still support single attribute rolling)

---

## 📊 Iteration Log

| Iteration | Directory | Main Issue | Solution |
|------|------|---------|---------  |
| 1 | `2026-01-25_DM_Agent_Debug` | Gemini 503 error | Changed model to `gemini-1.5-flash` |
| 2 | `2026-01-25_DM_Agent_Refactor` | Batch dice rolling requirement | Modified tool and prompt |
| 3 | `2026-01-25_DM_Agent_OpenAI` | Switch to OpenAI compatible interface | Modified provider config |
| 4 | `2026-01-25_DM_Agent_ProviderFix` | Provider not registered | Added `@register_provider` |
| 5 | `2026-01-26_DM_Agent_URLFix` | Base URL 404 error | URL cleaning logic |
| 6 | `2026-01-26_DM_Agent_ComprehensiveTest` | Comprehensive testing | Created test script, verified complete flow |

---

## 🎓 Best Practices Summary

### 1. Provider Development

```python
# ✅ Complete Provider registration template
@register_provider("your_provider", [
    ProviderCapability.CHAT,
    ProviderCapability.TOOLS,
    ProviderCapability.STREAMING
])
class YourProvider(LLMProviderInterface):
    def __init__(self):
        super().__init__()
        self.provider_name = "your_provider"
        self.default_base_url = "https://..."
        self.default_model = "model-name"
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        # URL cleaning
        base_url = config.get('base_url') or self.default_base_url
        if base_url.endswith('/unwanted/suffix'):
            base_url = base_url.rsplit('/unwanted/suffix', 1)[0]
        
        # Initialize client...
```

### 2. Environment Configuration

```bash
# .env correct configuration example
OPENAI_COMPATIBLE_API_KEY=sk-xxx
OPENAI_COMPATIBLE_BASE_URL=https://api.example.com/v1  # ✅ Only to /v1

# ❌ Wrong example
OPENAI_COMPATIBLE_BASE_URL=https://api.example.com/v1/chat/completions
```

### 3. Agent Development

```python
# ToolCallAgent complete template
class YourAgent(ToolCallAgent):
    name: str = "agent_name"
    description: str = "Brief description"
    
    # ✅ Detailed system prompt
    system_prompt: str = """
    1. Clear role definition
    2. Clear workflow
    3. Tool usage examples (including parameter format)
    4. Precautions
    """
    
    # ✅ Concise next_step_prompt
    next_step_prompt: str = "Based on current state, decide next action."
    
    max_steps: int = 15
    
    available_tools: ToolManager = Field(
        default_factory=lambda: ToolManager([
            YourTool1(),
            YourTool2()
        ])
    )
```

### 4. Testing Strategy

```python
# Create layered tests
async def test_basic():      # Basic functionality
async def test_tools():      # Tool calling
async def test_agent():      # Agent complete flow
```

---

## 🚀 Successful Verification

Final successful run:
```bash
cd "d:\react Agent\spoon-core"
.\spoon-env\Scripts\python.exe examples/dm_agent/dm_agent_demo.py
```

**Test Results**:
- ✅ Using third-party OpenAI compatible API
- ✅ Model: `claude-sonnet-4-5-20250929`
- ✅ Tool calls working (batch dice rolling)
- ✅ Smooth dialogue, complete character creation
- ✅ Character sheet saved successfully

---

## 📁 Related Documentation

- Iteration log: `D:\react Agent\spoon-core\docs\AI协作\本地Agent\进行中\`
- Code location: `D:\react Agent\spoon-core\examples\dm_agent\`
- Provider implementation: `D:\react Agent\spoon-core\spoon_ai\llm\providers\`

---

## 💡 Key Takeaways

1. **Provider Ecosystem**: SpoonOS's Provider mechanism requires explicit registration, base classes don't auto-register
2. **URL Handling Pitfall**: OpenAI SDK's automatic URL concatenation can easily cause duplication, needs framework-level fault tolerance
3. **Environment Isolation**: Virtual environment is mandatory, cannot use system Python
4. **Agent Prompt Engineering**: System prompt must be detailed and synced with tool capabilities
5. **Iterative Testing**: Creating independent test scripts is more efficient than running demo directly

---

**Summary**: Although multiple problems were encountered, through collaboration between Antigravity and Codex, each problem was systematically solved, ultimately successfully implementing complete DM Agent functionality. This experience provides valuable reference for future SpoonOS development.
