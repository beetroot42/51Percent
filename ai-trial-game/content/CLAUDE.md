[根目录](../CLAUDE.md) > **content**

# Content 模块

> 游戏内容配置文件 (JSON)

## 变更记录 (Changelog)

| 时间 | 操作 | 说明 |
|------|------|------|
| 2026-01-28 11:54:54 | 创建 | 初始化模块文档 |

---

## 模块职责

- 存储案件背景信息
- 定义陪审员角色卡
- 配置证据内容
- 存储证人对话树

---

## 入口与启动

无需启动，JSON 文件由后端自动加载。

---

## 目录结构

```
content/
+-- case/
|   +-- dossier.json           # 案件卷宗
|   +-- evidence/
|       +-- chat_history.json  # 证据: 聊天记录
|       +-- log_injection.json # 证据: 日志注入
|       +-- safety_report.json # 证据: 安全报告
|       +-- _template.json     # 证据模板
+-- jurors/
|   +-- juror_chen.json        # 陪审员: Chen
|   +-- juror_liu.json         # 陪审员: Liu
|   +-- juror_wang.json        # 陪审员: Wang
|   +-- juror_zhang.json       # 陪审员: Zhang
|   +-- juror_li.json          # 陪审员: Li
|   +-- test_juror.json        # 测试用陪审员
|   +-- _template.json         # 陪审员模板
+-- witnesses/
    +-- tech_expert.json       # 证人: 技术专家
    +-- zhang_wei.json         # 证人: 张伟
    +-- _template.json         # 证人模板
```

---

## 数据模型

### 案件卷宗 (dossier.json)

```json
{
  "title": "案件卷宗 - AI-2024-001",
  "summary": "一起涉及AI具身机器人的命案...",
  "sections": [
    {
      "title": "案件基本信息",
      "content": "时间：2024年3月15日..."
    }
  ]
}
```

### 陪审员配置 (juror_*.json)

```json
{
  "id": "juror_chen",
  "name": "Chen",
  "age": 29,
  "occupation": "AI Software Engineer",
  "background": "技术背景描述...",
  "personality": ["Analytical", "Curious"],
  "speaking_style": "Technical but approachable",
  "initial_stance": 15,
  "topic_weights": {
    "technical_details": 20,
    "external_attack": 15,
    "victim_position": -5
  },
  "first_message": "I can follow technical arguments..."
}
```

#### 立场值说明

- `initial_stance`: 初始立场 (-100 到 100)
- 正值倾向无罪，负值倾向有罪
- 投票时 stance > 0 投无罪

#### 话题权重说明

| 话题 | 说明 |
|------|------|
| `technical_responsibility` | 技术责任 |
| `external_attack` | 外部攻击 |
| `ai_autonomy` | AI 自主性 |
| `emotional_appeal` | 情感诉求 |
| `legal_precedent` | 法律先例 |
| `victim_position` | 受害者立场 |
| `safety_measures` | 安全措施 |
| `corporate_responsibility` | 企业责任 |
| `social_impact` | 社会影响 |
| `technical_details` | 技术细节 |

### 证据 (evidence/*.json)

```json
{
  "id": "chat_history",
  "name": "聊天记录",
  "icon": "chat",
  "description": "机器人系统日志中的聊天记录",
  "content": "详细内容..."
}
```

### 证人对话树 (witnesses/*.json)

```json
{
  "id": "tech_expert",
  "name": "技术专家",
  "nodes": {
    "start": {
      "text": "您好，有什么问题?",
      "options": [
        {"text": "关于攻击的技术细节", "next": "attack_details"},
        {"text": "机器人的安全机制", "next": "safety"}
      ]
    },
    "attack_details": {
      "text": "这是一次典型的 prompt injection...",
      "options": []
    }
  }
}
```

---

## 常见问题 (FAQ)

**Q: 如何添加新陪审员?**
A: 复制 `_template.json`，修改内容，重命名为 `juror_xxx.json`。

**Q: 话题权重如何影响立场?**
A: 当对话涉及某话题时，权重值会加到立场值上。正权重增加无罪倾向。

**Q: 证人对话树格式?**
A: 使用 `nodes` 对象，每个节点有 `text` 和 `options`。

---

## 相关文件清单

| 文件 | 说明 |
|------|------|
| `case/dossier.json` | 案件卷宗 |
| `case/evidence/*.json` | 3 个证据文件 |
| `jurors/juror_*.json` | 5 个陪审员配置 |
| `witnesses/*.json` | 2 个证人对话树 |
| `*/_template.json` | 各类模板文件 |
