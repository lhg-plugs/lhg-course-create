<!-- About 简介（推送后填写到仓库 About 栏）：
课程制作专家：大纲到试听课，一门知识付费课从 0 到可交付 ｜ 一键安装：/plugin marketplace add lhg-plugs/lhg-course-create
-->
<!-- topics（推送后打）：claude-code, claude-plugin, agent-skills, course-creation, online-course, quiz -->

# lhg-course-create：课程制作专家

> **一句话介绍**：主题→"痛点-方案-案例-行动"四段式大纲→口语化逐节讲义→记忆/理解/应用三档习题→试听课引流脚本，一门知识付费课从 0 到可交付，大纲-讲义-习题一致性自动审计。
>
> **一键安装**：在 Claude Code 里运行
> ```
> /plugin marketplace add lhg-plugs/lhg-course-create
> /plugin install lhg-course-create@lhg-plugs
> ```

## 它是什么

`lhg-course-create` 是一个 Claude Code 插件（plugin 为主、skill 为辅），专为"知识博主/培训师"设计：

- **4 个命令**（小白入口）：`course` 完整课程制作（主题→大纲→讲义→习题→试听课），`course-outline` 大纲单发，`course-quiz` 习题单发，`course-audit` 一致性自检
- **4 个平台中立 skill**（方法论，可移植到豆包/Workbuddy 等 agent 平台）：四段式大纲、讲义口语化转换 12 条、习题难度梯度、试听课引流脚本
- **3 个专家 agent**：大纲架构师、讲义撰写师、习题质检员
- **1 个硬门 hook**：课程交付前自动跑一致性审计，缺讲义/缺答案直接拦截（可一键豁免，不骚扰）
- **20 条确定性自查规则**：大纲-讲义映射、习题覆盖、四段式完整性、口语化、难度梯度，纯 Python、零第三方依赖，秒级出结果

工作流：`course-outline`（大纲先行）→ `course`（讲义+习题+试听课）→ `course-audit`（交付前自检），也可以只用其中一段。

## 4 个命令用法

| 命令 | 作用 | 示例 |
|---|---|---|
| `/lhg-course-create:course` | 完整课程制作：主题→大纲→讲义→习题→试听课→审计 | `/lhg-course-create:course 小白做短视频 零基础新手` |
| `/lhg-course-create:course-outline` | 大纲单发：三问→四段式大纲→评审→拍板 | `/lhg-course-create:course-outline 剪映入门 宝妈` |
| `/lhg-course-create:course-quiz` | 习题单发：三档难度→答案解析→一致性检查 | `/lhg-course-create:course-quiz 第1章讲义` |
| `/lhg-course-create:course-audit` | 一致性自检（脚本 + 人工评审清单） | `/lhg-course-create:course-audit ./delivery/ --strict` |

## 自查说明

自查 = 确定性脚本（机器）+ 人工评审清单（人）：

1. 先跑 `scripts/audit/course_audit.py`（20 条规则：一致性 3、大纲 3、讲义 4、习题 4、试听课 3、通用 3），零 LLM 成本；
2. 发现分三级：**blocker**（缺大纲/缺讲义/习题缺答案，必须补，交付前 hook 会拦截）、**warning**（习题零覆盖/四段式缺失，修或写豁免理由）、**nit**（顺手修）；
3. 再按各 skill 的人工清单过一遍脚本抓不到的（大纲三问、讲义读出声、试听课只讲 1 个方法）。

blocker 清零才算做完；为清零改规则算作弊，不许。

## 什么时候用 / 什么时候不用

**用它，当你**：
- 想做一门知识付费课，从大纲到讲义到习题到试听课，一次配齐
- 已有课程但完课率低，想系统检查大纲/讲义/习题的链路
- 担心"讲了没练""练了没答案"，想让习题真正形成学习闭环

**别用它，当你**：
- 做的是 K12 应试课程——本插件按成人知识付费设计（痛点-行动导向），课标对齐请用 `lhg-lesson-plan`
- 只想写单篇教程/文章——杀鸡不用牛刀，直接写就行
- 希望 AI 替你讲课——插件产出的是"课的资产"（大纲/讲义/习题/试听脚本），讲课还得你自己上

## 目录结构

```
lhg-course-create/
├── .claude-plugin/          # plugin.json（插件清单）+ marketplace.json（本仓即市场）
├── commands/                # 4 个命令：course / course-outline / course-quiz / course-audit
├── skills/                  # 4 个平台中立 skill（大纲/讲义/习题/试听课）
├── agents/                  # 3 个专家 agent（outline-architect / lecturer / quiz-checker）
├── hooks/                   # 1 个硬门（交付前一致性审计）+ 豁免说明
├── scripts/audit/           # 20 条确定性自查规则（零第三方依赖）
├── fixtures/                # 冒烟测试用例（坏/好对照）
├── smoke_test.py            # 一键冒烟测试
├── ATTRIBUTION.md           # 灵感来源与许可声明
└── LICENSE                  # MIT
```

## lhg-plugs 插件矩阵

| 插件 | 一句话 | 安装 |
|---|---|---|
| [lhg-course-create](https://github.com/lhg-plugs/lhg-course-create) | 课程制作专家：大纲到试听课，一门课从 0 到可交付 | `/plugin install lhg-course-create@lhg-plugs` |
| [lhg-fullstack](https://github.com/lhg-plugs/lhg-fullstack) | 小白一句话 → 高质量全栈应用 | `/plugin install lhg-fullstack@lhg-plugs` |
| [lhg-video-edit](https://github.com/lhg-plugs/lhg-video-edit) | 一句话把口播素材剪成爆款短视频（+口播脚本子命令） | `/plugin install lhg-video-edit@lhg-plugs` |

> 完整矩阵见组织模板仓 [lhg-fullstack](https://github.com/lhg-plugs/lhg-fullstack#lhg-plugs-插件矩阵)。

## 自检与反馈

本插件自带质检：每次使用后可跑 `python3 smoke_test.py` 一键验证（JSON 合法、skill/command/agent 完整性、20 条规则、fixtures 命中、hooks 行为）。

发现 bug 或有改进建议，以 `[QC] <一句话问题>` 为标题提交到 https://github.com/lhg-plugs/lhg-course-create/issues，正文写清"复现步骤 → 实际表现 → 期望表现"。

## 出品：刘洪光

本插件由真人出镜 IP「刘洪光」（安徽合肥）出品，归属 [lhg-skills](https://github.com/lhg-skills)。

- GitHub 主页：https://github.com/lhg-skills —— 全部 skill 开源在此，欢迎 star
- 抖音：搜「刘老师讲AI实战」
- 微信：lhgsmsw
