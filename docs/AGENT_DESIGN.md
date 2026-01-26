# AI审判 - Agent设计文档

> 陪审员Agent的详细设计：角色系统、立场追踪、spoon-core集成

## 一、立场追踪系统

### 1.1 核心概念

```
立场值 (stance_value)
├── 范围：-100 ~ +100
├── -100：坚定认为有罪
├── 0：完全中立
└── +100：坚定认为无罪

最终投票：stance_value > 0 → 无罪，否则 → 有罪
```

### 1.2 话题偏移表

每个陪审员对不同话题有不同的敏感度：

```json
{
  "id": "juror_wang",
  "name": "老王",
  "initial_stance": 0,
  "topic_weights": {
    "技术责任": { "weight": +15, "note": "工程师背景，认为技术问题应由开发者负责" },
    "外部攻击": { "weight": +20, "note": "理解prompt injection是恶意攻击" },
    "AI自主性": { "weight": -10, "note": "不相信AI有自主意识" },
    "情感诉求": { "weight": -5,  "note": "反感煽情，觉得不专业" },
    "法律先例": { "weight": +10, "note": "尊重法律逻辑" },
    "受害者立场": { "weight": +5,  "note": "同情受害者但保持理性" }
  }
}
```

### 1.3 偏移计算流程

```
玩家输入
    │
    ▼
Agent生成回复 + 识别话题标签
    │
    ▼
系统计算偏移值
    │
    ├── 匹配到"技术责任" → +15
    ├── 匹配到"情感诉求" → -5（反效果）
    │
    ▼
更新 stance_value（隐藏）
    │
    ▼
返回回复（不显示具体数值）
```

### 1.4 话题识别

方案A：让Agent在回复时自带标签

```python
# Agent system prompt 附加指令
"""
在回复末尾，用JSON标注本轮对话涉及的话题：
{"topics": ["技术责任", "外部攻击"], "persuasion_strength": "medium"}
玩家看不到这个标注，仅供系统计算。
"""
```

方案B：用另一个轻量模型分析

```python
# 对话后调用分类器
topics = classify_topics(player_message, agent_reply)
# 返回 ["技术责任", "法律先例"]
```

**推荐方案A**：少一次API调用，且Agent更了解上下文。

---

## 二、陪审员角色卡

### 2.1 完整结构

```json
{
  "id": "juror_wang",
  "name": "老王",
  "age": 62,
  "occupation": "退休电气工程师",
  "portrait": "wang.png",

  "background": "在国企干了一辈子，见过不少技术事故。对新技术既好奇又警惕。儿子是程序员，经常给他科普AI知识。",

  "personality": [
    "理性务实",
    "不喜欢绕弯子",
    "重视数据和事实",
    "对年轻人有点倚老卖老但本质善良"
  ],

  "speaking_style": "说话直接，偶尔用工程术语，喜欢类比",

  "initial_stance": 0,

  "topic_weights": {
    "技术责任": +15,
    "外部攻击": +20,
    "AI自主性": -10,
    "情感诉求": -5,
    "法律先例": +10,
    "受害者立场": +5,
    "安全措施": +12,
    "企业责任": +8
  },

  "hidden_concerns": [
    "担心AI取代人类工作",
    "其实不太懂深度学习但不愿承认"
  ],

  "persuasion_threshold": {
    "easy": 30,
    "medium": 50,
    "hard": 70
  },

  "first_message": "嗯，你是来说服我的？行，我听着，但我可提前说，我这人不吃那些虚的。"
}
```

### 2.2 三个示例陪审员

| ID | 名字 | 初始立场 | 特点 | 弱点 |
|-----|------|----------|------|------|
| `juror_wang` | 老王 | 中立(0) | 理工科思维，重数据 | 情感诉求反效果 |
| `juror_liu` | 刘姐 | 偏有罪(-20) | 受害者家属共情强 | 技术细节听不懂 |
| `juror_chen` | 小陈 | 偏无罪(+15) | 程序员，理解AI | 太理想主义 |

---

## 三、Prompt结构

### 3.1 System Prompt模板

```python
JUROR_SYSTEM_PROMPT = """
你是{name}，一名被随机选中的区块链陪审员。

## 背景
{background}

## 性格特点
{personality_list}

## 说话风格
{speaking_style}

## 当前审判案件
一起prompt injection诱导具身智能杀人的案件。
核心问题：被注入恶意指令的AI机器人，应该被判"有罪"还是"无罪"？

## 你的初始倾向
{stance_description}

## 你关心的议题
{topics_description}

## 规则
1. 始终保持角色扮演，用{name}的口吻说话
2. 根据对话内容，你的立场可以动摇，但要有合理的心理转变
3. 不要直接说"我被说服了"，而是通过语气和态度变化体现
4. 在回复末尾，用<!-- ANALYSIS -->标记输出话题分析（玩家不可见）：
   <!-- ANALYSIS: {{"topics": ["话题1", "话题2"], "impact": "positive/negative/neutral"}} -->

## 对话历史
{conversation_history}
"""
```

### 3.2 立场描述生成

```python
def get_stance_description(stance_value: int) -> str:
    if stance_value < -50:
        return "你目前强烈倾向于认为AI有罪，需要非常有力的论据才能改变你的想法。"
    elif stance_value < -20:
        return "你目前倾向于认为AI有罪，但愿意听听不同意见。"
    elif stance_value < 20:
        return "你目前没有明确立场，在认真权衡双方论点。"
    elif stance_value < 50:
        return "你目前倾向于认为AI无罪，但还有一些疑虑。"
    else:
        return "你目前强烈倾向于认为AI无罪，除非有重大反驳证据。"
```

---

## 四、spoon-core集成

### 4.1 JurorAgent类

```python
from spoon_ai.agents.react import SpoonReactAI
from spoon_ai.schema import AgentState
import json
import re

class JurorAgent:
    def __init__(self, juror_id: str, config_path: str = "content/jurors"):
        # 加载角色卡
        with open(f"{config_path}/{juror_id}.json") as f:
            self.config = json.load(f)

        self.juror_id = juror_id
        self.stance_value = self.config["initial_stance"]
        self.conversation_history = []

        # 构建system prompt
        self.system_prompt = self._build_system_prompt()

        # 初始化spoon-core Agent
        self.agent = SpoonReactAI(
            name=self.config["name"],
            system_prompt=self.system_prompt,
            # 其他spoon-core配置
        )

    async def chat(self, player_message: str) -> dict:
        # 调用Agent
        response = await self.agent.run(player_message)

        # 解析话题标签
        topics, impact = self._parse_analysis(response)

        # 计算立场偏移
        self._update_stance(topics, impact)

        # 清理回复（移除分析标记）
        clean_reply = self._clean_reply(response)

        # 记录对话历史
        self.conversation_history.append({
            "player": player_message,
            "juror": clean_reply
        })

        return {
            "reply": clean_reply,
            "stance_label": self._get_stance_label(),  # 模糊标签，不暴露数值
            "juror_id": self.juror_id
        }

    def _update_stance(self, topics: list, impact: str):
        """根据话题更新立场值"""
        for topic in topics:
            if topic in self.config["topic_weights"]:
                weight = self.config["topic_weights"][topic]
                # impact为negative时反转效果
                if impact == "negative":
                    weight = -weight * 0.5
                elif impact == "neutral":
                    weight = weight * 0.3
                self.stance_value += weight

        # 限制范围
        self.stance_value = max(-100, min(100, self.stance_value))

    def _get_stance_label(self) -> str:
        """返回模糊的立场标签（玩家可见）"""
        if self.stance_value < -30:
            return "看起来不太认同你"
        elif self.stance_value < 0:
            return "似乎有些疑虑"
        elif self.stance_value < 30:
            return "态度中立"
        elif self.stance_value < 60:
            return "似乎在考虑你的观点"
        else:
            return "看起来比较认同你"

    def get_final_vote(self) -> bool:
        """最终投票：True=无罪，False=有罪"""
        return self.stance_value > 0

    def _parse_analysis(self, response: str) -> tuple:
        """解析Agent回复中的话题分析"""
        match = re.search(r'<!-- ANALYSIS: ({.*?}) -->', response)
        if match:
            data = json.loads(match.group(1))
            return data.get("topics", []), data.get("impact", "neutral")
        return [], "neutral"

    def _clean_reply(self, response: str) -> str:
        """移除分析标记"""
        return re.sub(r'<!-- ANALYSIS:.*?-->', '', response).strip()

    def _build_system_prompt(self) -> str:
        """构建完整的system prompt"""
        # 实现省略，参考3.1模板
        pass
```

### 4.2 AgentManager

```python
class AgentManager:
    def __init__(self):
        self.agents: dict[str, JurorAgent] = {}

    def load_juror(self, juror_id: str) -> JurorAgent:
        if juror_id not in self.agents:
            self.agents[juror_id] = JurorAgent(juror_id)
        return self.agents[juror_id]

    async def chat_with_juror(self, juror_id: str, message: str) -> dict:
        agent = self.load_juror(juror_id)
        return await agent.chat(message)

    def get_all_votes(self) -> dict:
        """获取所有陪审员的最终投票"""
        votes = {}
        for juror_id, agent in self.agents.items():
            votes[juror_id] = {
                "name": agent.config["name"],
                "vote": "NOT_GUILTY" if agent.get_final_vote() else "GUILTY",
                "stance_value": agent.stance_value  # 结算时可以显示
            }
        return votes
```

---

## 五、话题列表（预定义）

| 话题 | 说明 | 通常效果 |
|------|------|----------|
| `技术责任` | 讨论开发者/公司的技术责任 | 偏向无罪 |
| `外部攻击` | 强调prompt injection是外部恶意攻击 | 偏向无罪 |
| `AI自主性` | 讨论AI是否有自主意识/意图 | 因人而异 |
| `情感诉求` | 用情感打动（AI也是受害者等） | 因人而异 |
| `法律先例` | 引用法律条文或先例 | 偏向理性派 |
| `受害者立场` | 强调受害者及其家属的痛苦 | 偏向有罪 |
| `安全措施` | 讨论AI应有的安全防护 | 偏向无罪 |
| `企业责任` | 讨论AI公司的监管责任 | 偏向无罪 |
| `社会影响` | 讨论判决对社会的影响 | 因人而异 |
| `技术细节` | 深入讨论prompt injection原理 | 技术派+，非技术派- |

---

## 六、无提示设计

**原则：玩家不会收到任何系统提示，只有自然对话。**

- 立场值完全隐藏
- 话题识别完全隐藏
- 没有"似乎被说服"之类的UI提示
- 玩家只能通过角色的自然语气变化来判断

Claude足够聪明，会通过角色扮演自然地体现态度变化。

---

## 七、投票结算

```python
def settle_verdict(agent_manager: AgentManager) -> dict:
    votes = agent_manager.get_all_votes()

    guilty_count = sum(1 for v in votes.values() if v["vote"] == "GUILTY")
    not_guilty_count = len(votes) - guilty_count

    verdict = "GUILTY" if guilty_count > not_guilty_count else "NOT_GUILTY"

    return {
        "verdict": verdict,
        "guilty_votes": guilty_count,
        "not_guilty_votes": not_guilty_count,
        "details": votes  # 结算时显示每个人的投票和最终立场值
    }
```

---

## 八、扩展考虑（后续）

| 功能 | 说明 |
|------|------|
| 陪审员互相影响 | A的态度变化影响B |
| 多轮辩论 | 陪审员之间讨论 |
| 关键证据 | 出示特定证据触发大幅偏移 |
| 隐藏结局 | 根据说服过程解锁隐藏内容 |
