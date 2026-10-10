#!/usr/bin/env python3
"""lhg-course-create 确定性课程审计：20 条规则，零第三方依赖。

扫描交付目录（delivery/）下的课程资产，做一致性检查：
  outline.md        课程大纲（## 第N章：标题，节内应含痛点/方案/案例/行动）
  lectures/chN.md   逐节讲义（与大纲章节一一对应）
  quiz/chN.md       配套习题（每章 >=3 道，难度标签记忆/理解/应用，带答案解析）
  trial.md          试听课引流脚本（可选；有则检查钩子与转化引导）

输出 JSON 与人类可读报告；有 blocker 时以 exit code 2 退出
（供 hooks 与 CI 使用）。

用法：
    python3 course_audit.py --target <目录> [--format json|text] [--fail-on blocker|warning|nit]

规则文案与检测逻辑均为本项目原创；公开检索（2026-10-11）未发现
知识付费课程制作方向的垂直 skill，方法论为独立撰写。
详见仓库 ATTRIBUTION.md。
"""

import argparse
import json
import os
import re
import sys

VERSION = "1.0.0"
TOOL = "lhg-course-create/course-audit"

SKIP_DIRS = {".git", "__pycache__", "node_modules", "dist", "build"}

# ---------------------------------------------------------------- 规则注册表
RULES = [
    # ---- 一致性（blocker/warning）----
    ("CONS-MAP-001", "blocker", "一致性",
     "大纲第 {n} 章无对应讲义", "大纲写了，讲义没写——课程链路断了，先补讲义再交付。"),
    ("CONS-QUIZ-001", "warning", "一致性",
     "大纲第 {n} 章零习题覆盖", "该章没有配套习题文件，学员学完无处练习，完课率会掉。"),
    ("CONS-TRIAL-001", "warning", "一致性",
     "缺少试听课引流脚本", "没有 trial.md，试听课靠临场发挥，转化看天。"),
    # ---- 大纲（warning）----
    ("OUT-STRUCT-001", "warning", "大纲",
     "第 {n} 章缺少四段式要素：{missing}", "大纲每章应含痛点-方案-案例-行动四段，缺了学员不知道\"跟我有什么关系\"。"),
    ("OUT-SCOPE-001", "warning", "大纲",
     "大纲共 {n} 章，规模异常", "少于 3 章撑不起一门课，多于 12 章学员学不完，建议拆课。"),
    ("OUT-DUP-001", "warning", "大纲",
     "章节标题重复：{title}", "重复的章节标题会让学员困惑，合并或改名。"),
    # ---- 讲义（warning/nit）----
    ("LEC-TONE-001", "warning", "讲义",
     "书面语超标：{word}", "讲义是\"说\"出来的，不是\"写\"出来的，书面语念着拗口。"),
    ("LEC-LONG-001", "warning", "讲义",
     "超长句（>{n}字）", "一句话太长，学员听/看到一半就丢了，拆短。"),
    ("LEC-ORAL-001", "nit", "讲义",
     "第二人称过少", "多用\"你\"，少用\"学员们\"——课程是讲给\"一个人\"听的。"),
    ("LEC-CASE-001", "nit", "讲义",
     "讲义缺少案例", "光讲道理不讲故事，学员记不住，加 1 个案例。"),
    # ---- 习题（blocker/warning）----
    ("QUIZ-ANS-001", "blocker", "习题",
     "习题缺少答案/解析：{file}", "没答案的习题是半成品，学员做完不知道对错。"),
    ("QUIZ-GRAD-001", "warning", "习题",
     "难度梯度缺档：{missing}", "习题应覆盖记忆→理解→应用三档，缺档说明能力目标没闭环。"),
    ("QUIZ-NUM-001", "warning", "习题",
     "习题数量不足：{file} 仅 {n} 道", "每章至少 3 道题，少了测不出掌握度。"),
    ("QUIZ-FMT-001", "nit", "习题",
     "习题缺少题型标注", "建议标注[单选]/[简答]等题型，学员有预期。"),
    # ---- 试听课（warning）----
    ("TRIAL-HOOK-001", "warning", "试听课",
     "试听课脚本缺少钩子", "试听课前 3 分钟没有钩子（福利/悬念/痛点），观众直接走。"),
    ("TRIAL-CTA-001", "warning", "试听课",
     "试听课缺少转化引导", "没出现报名/购买/扫码/链接类引导词，听完就散了。"),
    ("TRIAL-LEN-001", "nit", "试听课",
     "试听课脚本过长", "试听课讲 20–30 分钟最合适，太长等于剧透正课。"),
    # ---- 通用 ----
    ("GEN-EMPTY-001", "warning", "通用",
     "空文件：{file}", "空文件混进交付目录，删掉或补上。"),
    ("GEN-ENC-001", "nit", "通用",
     "文件无法解码：{file}", "非 UTF-8 文件，确认不是乱码。"),
    ("GEN-NOOUTLINE-001", "blocker", "通用",
     "缺少 outline.md", "没有大纲，一切无从谈起，先写大纲。"),
]

FOUR_PARTS = ["痛点", "方案", "案例", "行动"]
DIFF_TAGS = ["记忆", "理解", "应用"]
WRITTEN_WORDS = ["进行", "予以", "综上所述", "鉴于", "特此", "贯彻落实",
                 "众所周知", "不言而喻"]
TRIAL_HOOKS = ["钩子", "福利", "悬念", "免费", "痛点", "前 3 分钟"]
TRIAL_CTAS = ["报名", "购买", "扫码", "链接", "下单", "咨询", "加微信"]


class Finding:
    __slots__ = ("rule_id", "severity", "category", "title", "file", "line",
                 "snippet", "detail")

    def __init__(self, rule_id, severity, category, title, file, line,
                 snippet, detail):
        self.rule_id = rule_id
        self.severity = severity
        self.category = category
        self.title = title
        self.file = file
        self.line = line
        self.snippet = snippet
        self.detail = detail

    def to_dict(self):
        return {"rule_id": self.rule_id, "severity": self.severity,
                "category": self.category, "title": self.title,
                "file": self.file, "line": self.line,
                "snippet": self.snippet, "detail": self.detail}


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except UnicodeDecodeError:
        return None
    except OSError:
        return ""


def chapter_headers(text):
    """返回 [(章号, 标题行, 节正文)]。"""
    out, cur = [], None
    for ln in text.split("\n"):
        m = re.match(r"^#{1,3}\s*第(\d+)章[:：]?\s*(.*)$", ln.strip())
        if m:
            if cur:
                out.append(cur)
            cur = (int(m.group(1)), ln.strip(), [])
        elif cur:
            cur[2].append(ln)
    if cur:
        out.append(cur)
    return [(n, t, "\n".join(b)) for n, t, b in out]


def audit_target(target):
    findings = []
    outline_p = os.path.join(target, "outline.md")
    lec_dir = os.path.join(target, "lectures")
    quiz_dir = os.path.join(target, "quiz")
    trial_p = os.path.join(target, "trial.md")

    def add(rule_id, file="", line=0, snippet="", **fmt):
        rid, sev, cat, title_tpl, detail = next(
            r for r in RULES if r[0] == rule_id)
        findings.append(Finding(rid, sev, cat, title_tpl.format(file=file, **fmt),
                                file, line, snippet[:80], detail))

    # ---- 大纲存在性 ----
    outline = read_text(outline_p)
    if outline is None:
        add("GEN-ENC-001", file="outline.md")
        return findings
    if not outline:
        if not os.path.isfile(outline_p):
            add("GEN-NOOUTLINE-001", file="outline.md")
        else:
            add("GEN-EMPTY-001", file="outline.md")
        return findings

    chapters = chapter_headers(outline)
    if not chapters:
        add("GEN-NOOUTLINE-001", file="outline.md",
            snippet="未识别到「第N章」标题")
        return findings

    # ---- 大纲规模与重复 ----
    if len(chapters) < 3 or len(chapters) > 12:
        add("OUT-SCOPE-001", file="outline.md", n=len(chapters))
    seen = {}
    for n, title, _ in chapters:
        seen.setdefault(title, []).append(n)
    for title, ns in seen.items():
        if len(ns) > 1:
            add("OUT-DUP-001", file="outline.md", title=title[:20])

    # ---- 逐章：四段式 + 讲义映射 + 习题覆盖 ----
    for n, title, body in chapters:
        missing = [p for p in FOUR_PARTS if p not in body and p not in title]
        if len(missing) >= 2:
            add("OUT-STRUCT-001", file="outline.md", n=n,
                missing="、".join(missing))

        lec_p = os.path.join(lec_dir, "ch%d.md" % n)
        lec = read_text(lec_p) if os.path.isfile(lec_p) else None
        if lec is None:
            add("CONS-MAP-001", file="lectures/ch%d.md" % n, n=n)
        else:
            if not lec.strip():
                add("GEN-EMPTY-001", file="lectures/ch%d.md" % n)
            else:
                audit_lecture(lec, n, add)

        quiz_p = os.path.join(quiz_dir, "ch%d.md" % n)
        quiz = read_text(quiz_p) if os.path.isfile(quiz_p) else None
        if quiz is None:
            add("CONS-QUIZ-001", file="quiz/ch%d.md" % n, n=n)
        else:
            audit_quiz(quiz, n, "quiz/ch%d.md" % n, add)

    # ---- 试听课 ----
    trial = read_text(trial_p) if os.path.isfile(trial_p) else None
    if trial is None:
        add("CONS-TRIAL-001", file="trial.md")
    elif trial.strip():
        if not any(w in trial for w in TRIAL_HOOKS):
            add("TRIAL-HOOK-001", file="trial.md")
        if not any(w in trial for w in TRIAL_CTAS):
            add("TRIAL-CTA-001", file="trial.md")
        if len(re.sub(r"\s", "", trial)) > 6000:
            add("TRIAL-LEN-001", file="trial.md")
    else:
        add("GEN-EMPTY-001", file="trial.md")

    return findings


def audit_lecture(text, n, add):
    fname = "lectures/ch%d.md" % n
    hits = {}
    for w in WRITTEN_WORDS:
        c = text.count(w)
        if c:
            hits[w] = c
    if hits:
        top = max(hits, key=hits.get)
        add("LEC-TONE-001", file=fname, word="%s（共 %d 处）"
            % (top, sum(hits.values())))
    for i, ln in enumerate(text.split("\n"), 1):
        clean = re.sub(r"\s", "", ln)
        if len(clean) > 40 and not ln.strip().startswith(("#", "|", "-", ">")):
            add("LEC-LONG-001", file=fname, line=i,
                snippet=clean[:40], n=40)
    you_count = len(re.findall(r"你", text))
    if you_count < 3 and len(re.sub(r"\s", "", text)) > 300:
        add("LEC-ORAL-001", file=fname)
    if "案例" not in text and "比如" not in text and "例如" not in text:
        add("LEC-CASE-001", file=fname)


def audit_quiz(text, n, fname, add):
    if not text.strip():
        add("GEN-EMPTY-001", file=fname)
        return
    # 题目数：以 "1." / "Q1" / "第1题" 开头的行
    q_lines = [ln for ln in text.split("\n")
               if re.match(r"^\s*(\d+[.、]|Q\d+|第\d+题)", ln)]
    nq = len(q_lines) if q_lines else (1 if "?" in text or "？" in text else 0)
    if nq < 3:
        add("QUIZ-NUM-001", file=fname, n=nq)
    if "答案" not in text and "解析" not in text:
        add("QUIZ-ANS-001", file=fname)
    missing = [t for t in DIFF_TAGS if t not in text]
    if missing:
        add("QUIZ-GRAD-001", file=fname, missing="、".join(missing))
    if not re.search(r"\[?(单选|多选|简答|判断)", text):
        add("QUIZ-FMT-001", file=fname)


def summarize(findings):
    s = {"blocker": 0, "warning": 0, "nit": 0, "rules_run": len(RULES)}
    for f in findings:
        if f.severity in s:
            s[f.severity] += 1
    return s


def to_text(findings, summary):
    lines = ["[%s v%s] 发现 %d 项（blocker=%d, warning=%d, nit=%d）"
             % (TOOL, VERSION, len(findings), summary["blocker"],
                summary["warning"], summary["nit"])]
    sev_order = {"blocker": 0, "warning": 1, "nit": 2}
    for f in sorted(findings, key=lambda x: (sev_order[x.severity], x.rule_id)):
        loc = "%s:%d" % (f.file, f.line) if f.line else f.file
        lines.append("[%s] %s %s — %s" % (f.severity.upper(), f.rule_id, loc,
                                          f.title))
        if f.snippet:
            lines.append("        ▸ %s" % f.snippet)
        lines.append("        %s" % f.detail)
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True)
    ap.add_argument("--format", choices=["json", "text"], default="text")
    ap.add_argument("--fail-on", choices=["blocker", "warning", "nit"],
                    default="blocker")
    args = ap.parse_args()

    if not os.path.isdir(args.target):
        print("target 不存在：%s" % args.target, file=sys.stderr)
        return 1

    findings = audit_target(args.target)
    summary = summarize(findings)

    if args.format == "json":
        print(json.dumps({"tool": TOOL, "version": VERSION,
                          "summary": summary,
                          "findings": [f.to_dict() for f in findings]},
                         ensure_ascii=False, indent=2))
    else:
        print(to_text(findings, summary))

    order = {"blocker": 0, "warning": 1, "nit": 2}
    thresh = order[args.fail_on]
    worst = min([order[f.severity] for f in findings], default=99)
    return 2 if worst <= thresh else 0


if __name__ == "__main__":
    sys.exit(main())
