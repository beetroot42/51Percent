# Phase 0: 准备工作

## 目标

创建新目录结构，清理旧内容文件，创建所有占位符模板。

---

## 任务清单

### P0.1 创建新目录

```
content/
├── story/           # 新建
├── triggers/        # 新建
└── prompts/         # 新建
```

### P0.2 清理旧文件

| 删除路径 | 说明 |
|----------|------|
| `content/jurors/juror_chen.json` | 旧陪审员 |
| `content/jurors/juror_li.json` | 旧陪审员 |
| `content/jurors/juror_liu.json` | 旧陪审员 |
| `content/jurors/juror_wang.json` | 旧陪审员 |
| `content/jurors/juror_zhang.json` | 旧陪审员 |
| `content/jurors/test_juror.json` | 测试用 |
| `content/witnesses/tech_expert.json` | 旧证人 |
| `content/witnesses/zhang_wei.json` | 旧证人 |
| `content/case/evidence/chat_history.json` | 旧证据 |
| `content/case/evidence/log_injection.json` | 旧证据 |
| `content/case/evidence/safety_report.json` | 旧证据 |

**保留：** `_template.json` 文件（参考用）

### P0.3 创建占位符内容文件

#### 叙事文件

| 文件 | 内容 |
|------|------|
| `content/story/opening.json` | 世界观滚动文本 |
| `content/story/blake.json` | Blake 3轮×3选项对话树 |
| `content/story/ending_guilty.json` | 有罪结局文本 |
| `content/story/ending_not_guilty.json` | 无罪结局文本 |
| `content/story/ending_betrayal.json` | 背叛结局文本 |

#### 证物文件 (E1-E15)

| 文件 | ID | 名称 |
|------|----|------|
| `content/case/evidence/E01_jailbreak_chat.json` | E1 | 越狱对话记录 |
| `content/case/evidence/E02_behavior_log.json` | E2 | AI行为日志 |
| `content/case/evidence/E03_health_access.json` | E3 | 健康档案访问记录 |
| `content/case/evidence/E04_emergency_record.json` | E4 | 急救执行记录 |
| `content/case/evidence/E05_lab_surveillance.json` | E5 | 实验室监控记录 |
| `content/case/evidence/E06_architecture_doc.json` | E6 | 架构文档 |
| `content/case/evidence/E07_seldon_profile.json` | E7 | 谢顿档案 |
| `content/case/evidence/E08_dors_profile.json` | E8 | 铎丝档案 |
| `content/case/evidence/E09_cleon_profile.json` | E9 | 克里昂档案 |
| `content/case/evidence/E10_daneel_profile.json` | E10 | 丹尼尔档案 |
| `content/case/evidence/E11_seldon_testimony.json` | E11 | 谢顿的证词 (解锁) |
| `content/case/evidence/E12_dors_tech_testimony.json` | E12 | 铎丝的技术证词 (解锁) |
| `content/case/evidence/E13_daneel_instruction.json` | E13 | 丹尼尔指令解读陈述 (解锁) |
| `content/case/evidence/E14_daneel_emergency.json` | E14 | 丹尼尔急救决策陈述 (解锁) |
| `content/case/evidence/E15_daneel_tidying.json` | E15 | 丹尼尔整理行为陈述 (解锁) |

#### 证人文件

| 文件 | 角色 |
|------|------|
| `content/witnesses/seldon.json` | 谢顿（学生） |
| `content/witnesses/dors.json` | 铎丝（学姐） |
| `content/witnesses/daneel.json` | 丹尼尔（被告AI） |

#### 陪审员文件

| 文件 | 代号 |
|------|------|
| `content/jurors/j1_rationalist.json` | 理中客 |
| `content/jurors/j2_radical.json` | 激进者 |
| `content/jurors/j3_sympathizer.json` | 同情者 |
| `content/jurors/j4_opportunist.json` | 机奸 |
| `content/jurors/j5_philosopher.json` | 哲学家 |

#### 触发规则

| 文件 | 说明 |
|------|------|
| `content/triggers/evidence_triggers.json` | 证人+证物→新证物规则 |

#### Prompt 文件

| 文件 | 说明 |
|------|------|
| `content/prompts/common_prefix.md` | 所有 Agent 通用前缀 |
| `content/prompts/juror_suffix.md` | 陪审员专用后缀 |
| `content/prompts/daneel.md` | 被告AI专用 prompt |

### P0.4 重写卷宗

| 文件 | 说明 |
|------|------|
| `content/case/dossier.json` | 更新为新案件内容 |

---

## 验收标准

- [ ] 新目录 `story/`, `triggers/`, `prompts/` 存在
- [ ] 旧陪审员/证人/证据文件已删除
- [ ] 所有新 JSON 文件已创建（带占位符）
- [ ] 后端可启动不报错（加载新结构）
