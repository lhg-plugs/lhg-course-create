---
description: 完整课程制作：主题→课程大纲→逐节讲义→配套习题→试听课引流脚本，一门知识付费课从 0 到可交付。
argument-hint: [课程主题] [目标学员]
---

# /lhg-course-create:course —— 完整课程制作

用户输入在 `$ARGUMENTS` 中：`[课程主题] [目标学员]`。

全程按 `lhg-cc-outline` → `lhg-cc-lecture` → `lhg-cc-quiz` → `lhg-cc-trial` 顺序执行，最后用 `lhg-cc-*` 自查 + `course_audit.py` 审计。各阶段可分派给 `outline-architect` / `lecturer` / `quiz-checker` agent。

## 流程

### 1. 定主题与学员
- 主题一句话 + 目标学员一句话。太宽就收窄到"学完能做到 X"。
- 回答大纲三问（见 lhg-cc-outline 第 2 节）：学完能做到什么？学员最痛的 3 个点？凭什么是你讲？
- 三问答不上来 → 打回，不许往下写。

### 2. 写大纲
- 按四段式（痛点-方案-案例-行动）写 3–12 章大纲，每章一句话四段。
- **大纲先给用户确认**：大纲没拍板，不许写讲义。

### 3. 写逐节讲义
- 每章扩成讲义（20–30 分钟/节），按口语化 12 条转换（见 lhg-cc-lecture）。
- 每节结构：开场钩子 → 讲解（方法+案例）→ 互动 → 行动项。
- 写完读出声，拗口的重写。

### 4. 配习题
- 每章 ≥3 道，覆盖记忆→理解→应用三档，每题带答案解析。
- 习题必须能对应回大纲知识点，对应不上的删。

### 5. 写试听课脚本
- 按三标准选 1 章（痛点最强/有快速赢/不剧透核心）。
- 20 分钟脚本：钩子 → 痛点 → 1 个干货方法 → 转化三件套。

### 6. 一致性审计
- 输出到 `delivery/`（outline.md / lectures/chN.md / quiz/chN.md / trial.md），跑：
```bash
python3 scripts/audit/course_audit.py --target ./delivery/ --format text
```
- blocker（缺讲义/缺答案/缺大纲）必须清零；warning（习题零覆盖/缺试听课）修或写豁免理由。

## 硬规则
- 大纲没让用户确认就写讲义 → 不许。
- 讲义没口语化（书面语超标）→ 打回重写。
- 习题没答案 → 不许交付。
- blocker 没清零 → 不许交付。
