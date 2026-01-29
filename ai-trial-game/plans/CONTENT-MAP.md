# 内容文件位置索引

> **你更新文本该去哪？看这个文件。**

---

## 第一幕：接任务

| 内容 | 文件路径 | 状态 |
|------|----------|------|
| 世界观滚动文本 | `content/story/opening.json` | 待创建 |
| Blake 对话树 | `content/story/blake.json` | 待创建 |

---

## 第二幕：调查阶段

### 案件卷宗

| 内容 | 文件路径 | 状态 |
|------|----------|------|
| 案件基本信息 | `content/case/dossier.json` | 需重写 |

### 证物 (E1-E15)

| ID | 证物名称 | 文件路径 | 状态 |
|----|----------|----------|------|
| E1 | 越狱对话记录 | `content/case/evidence/E01_jailbreak_chat.json` | 待创建 |
| E2 | AI行为日志（72小时） | `content/case/evidence/E02_behavior_log.json` | 待创建 |
| E3 | 健康档案访问记录 | `content/case/evidence/E03_health_access.json` | 待创建 |
| E4 | 急救执行记录 | `content/case/evidence/E04_emergency_record.json` | 待创建 |
| E5 | 实验室监控记录 | `content/case/evidence/E05_lab_surveillance.json` | 待创建 |
| E6 | 架构文档 | `content/case/evidence/E06_architecture_doc.json` | 待创建 |
| E7 | 谢顿档案 | `content/case/evidence/E07_seldon_profile.json` | 待创建 |
| E8 | 铎丝档案 | `content/case/evidence/E08_dors_profile.json` | 待创建 |
| E9 | 克里昂档案 | `content/case/evidence/E09_cleon_profile.json` | 待创建 |
| E10 | 丹尼尔档案 | `content/case/evidence/E10_daneel_profile.json` | 待创建 |
| E11 | 谢顿的证词 | `content/case/evidence/E11_seldon_testimony.json` | 解锁：谢顿+E1 |
| E12 | 铎丝的技术证词 | `content/case/evidence/E12_dors_tech_testimony.json` | 解锁：铎丝+E6 |
| E13 | 丹尼尔关于指令解读的陈述 | `content/case/evidence/E13_daneel_instruction.json` | 解锁：丹尼尔+E1 |
| E14 | 丹尼尔关于急救决策的陈述 | `content/case/evidence/E14_daneel_emergency.json` | 解锁：丹尼尔+E3 |
| E15 | 丹尼尔关于整理行为的陈述 | `content/case/evidence/E15_daneel_tidying.json` | 解锁：丹尼尔+E5 |

### 证人

| 角色 | 文件路径 | 状态 |
|------|----------|------|
| 谢顿（学生） | `content/witnesses/seldon.json` | 待创建 |
| 铎丝（学姐） | `content/witnesses/dors.json` | 待创建 |
| 丹尼尔（被告AI） | `content/witnesses/daneel.json` | 待创建 |

### 证物触发规则

| 文件路径 | 说明 |
|----------|------|
| `content/triggers/evidence_triggers.json` | 证人+证物→新证物的触发规则 |

---

## 第三幕：陪审员

| 角色 | 代号 | 文件路径 | 状态 |
|------|------|----------|------|
| J1 | 理中客 | `content/jurors/j1_rationalist.json` | 待创建 |
| J2 | 激进者 | `content/jurors/j2_radical.json` | 待创建 |
| J3 | 同情者 | `content/jurors/j3_sympathizer.json` | 待创建 |
| J4 | 机奸 | `content/jurors/j4_opportunist.json` | 待创建 |
| J5 | 哲学家 | `content/jurors/j5_philosopher.json` | 待创建 |

---

## 结局

| 内容 | 文件路径 | 状态 |
|------|----------|------|
| 有罪结局 | `content/story/ending_guilty.json` | 待创建 |
| 无罪结局 | `content/story/ending_not_guilty.json` | 待创建 |
| 背叛结局（可选） | `content/story/ending_betrayal.json` | 待创建 |

---

## Agent Prompts

| 角色 | 文件路径 | 说明 |
|------|----------|------|
| 通用前缀 | `content/prompts/common_prefix.md` | 所有Agent共用 |
| 通用后缀（陪审员） | `content/prompts/juror_suffix.md` | 陪审员专用后缀 |
| 丹尼尔 prompt | `content/prompts/daneel.md` | 被告AI |
| J1-J5 prompts | 内嵌在各自 JSON 中 | 或单独 `content/prompts/j1.md` 等 |

---

## 目录结构预览

```
content/
├── case/
│   ├── dossier.json                    # 案件卷宗
│   └── evidence/
│       ├── E01_jailbreak_chat.json     # 越狱对话记录
│       ├── E02_behavior_log.json       # AI行为日志
│       ├── ...
│       └── E15_daneel_tidying.json     # 丹尼尔整理行为陈述
├── jurors/
│   ├── j1_rationalist.json             # 理中客
│   ├── j2_radical.json                 # 激进者
│   ├── j3_sympathizer.json             # 同情者
│   ├── j4_opportunist.json             # 机奸
│   └── j5_philosopher.json             # 哲学家
├── witnesses/
│   ├── seldon.json                     # 谢顿（学生）
│   ├── dors.json                       # 铎丝（学姐）
│   └── daneel.json                     # 丹尼尔（被告AI）
├── story/
│   ├── opening.json                    # 世界观滚动
│   ├── blake.json                      # Blake对话树
│   ├── ending_guilty.json              # 有罪结局
│   ├── ending_not_guilty.json          # 无罪结局
│   └── ending_betrayal.json            # 背叛结局
├── triggers/
│   └── evidence_triggers.json          # 证物触发规则
└── prompts/
    ├── common_prefix.md                # 通用prompt前缀
    ├── juror_suffix.md                 # 陪审员后缀
    └── daneel.md                       # 被告AI prompt
```
