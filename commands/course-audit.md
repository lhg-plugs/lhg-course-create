---
description: 课程一致性自检：对交付目录跑 20 条确定性规则（大纲-讲义-习题映射、习题覆盖、四段式、口语化），blocker 清零才算过。
argument-hint: [交付目录] [--strict]
---

# /lhg-course-create:course-audit —— 课程一致性自检

用户输入在 `$ARGUMENTS` 中：`[交付目录] [--strict]`。`--strict` = warning 也算失败（上线前用）。

全程加载各 skill 自查节，自检可分派给 `quiz-checker` agent 做交叉检查。

## 流程

### 1. 跑确定性脚本
```bash
python3 scripts/audit/course_audit.py --target <交付目录> --format text
# 严格模式：
python3 scripts/audit/course_audit.py --target <交付目录> --format text --fail-on warning
```

### 2. 分级处理
- **blocker**（缺大纲/缺讲义/习题缺答案）：必须补，补完重跑，直到清零。
- **warning**（习题零覆盖/缺试听课/四段式缺失）：修，或写豁免理由。
- **nit**（口语细节/题型标注）：顺手修。

### 3. 人工复核清单（脚本抓不到的）
- 大纲三问还成立吗？（做到什么/痛点/凭什么是你）
- 讲义读出声了吗？（拗口的重写）
- 试听课只讲了 1 个方法吗？（讲多了砍）
- 应用题有反馈机制吗？（没反馈没人交）

### 4. 交付审计报告
- 规则结果 + warning 豁免理由 + 人工复核结论，三者齐了才算交付完成。

## 硬规则
- blocker 没清零就交付 → 不许。
- 为清零改规则 → 作弊，不许。
- warning 无豁免理由直接忽略 → 不许。
