#!/usr/bin/env python3
"""lhg-course-create 硬门：课程交付前一致性检查。

触发：PreToolUse / Bash。脚本先判断本次 Bash 命令是否为"交付"
（命令含 course-create-deliver 标记——这是 /lhg-course-create:course
在用户确认交付时插入的标记），不是则 0 开销直接放行；是则对
delivery/ 目录跑 course_audit.py。

命中 blocker（缺大纲/缺讲义/习题缺答案）→ 拦截交付；
只有 warning/nit → 提醒式放行（additionalContext 列出缺口）。

逃生方式（按推荐度排序）：
  1. 补齐缺口后重新交付（推荐）。
  2. 紧急情况：LHG_CC_HOOKS_OFF=1 <交付命令>（单次豁免本次 hook）。
  3. /plugin disable lhg-course-create（整个插件停用，hooks 不再触发）。

设计原则：脚本内部出错（找不到审计脚本、解析失败等）时 fail-open
直接放行，不因插件自身故障骚扰用户；真正的门禁在
/lhg-course-create:course-audit。零第三方依赖。
"""

import json
import os
import re
import subprocess
import sys

DELIVER_RE = re.compile(r"course-create-deliver", re.I)


def main() -> int:
    # 逃生开关
    if os.environ.get("LHG_CC_HOOKS_OFF") == "1":
        return 0

    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0  # 输入解析失败：fail-open

    tool_input = payload.get("tool_input", {}) or {}
    command = tool_input.get("command", "") or ""

    # 非交付命令：快速放行
    if not DELIVER_RE.search(command):
        return 0

    try:
        return check_delivery(command)
    except Exception:
        return 0  # 校验自身出错：fail-open


def check_delivery(command):
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT") or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..")
    audit_py = os.path.join(plugin_root, "scripts", "audit", "course_audit.py")
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()

    # 允许命令里用 --target 指定目录，否则默认 delivery/
    m = re.search(r"--target\s+(\S+)", command)
    target = m.group(1) if m else os.path.join(project_dir, "delivery")
    if not os.path.isabs(target):
        target = os.path.normpath(os.path.join(project_dir, target))

    if not os.path.isdir(target):
        out = {"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "additionalContext": (
                "提醒：交付标记已触发，但未找到课程目录 %s。"
                "请先把大纲/讲义/习题放入 delivery/ 再交付，否则跳过此提醒。"
                % target)}}
        sys.stdout.write(json.dumps(out, ensure_ascii=False))
        return 0

    if not os.path.isfile(audit_py):
        return 0  # 审计脚本缺失：fail-open

    try:
        r = subprocess.run(
            [sys.executable, audit_py, "--target", target, "--format", "json"],
            capture_output=True, text=True, timeout=60)
        data = json.loads(r.stdout)
    except Exception:
        return 0  # 审计跑不起来：fail-open

    blockers = [f for f in data.get("findings", [])
                if f.get("severity") == "blocker"]
    warnings = [f for f in data.get("findings", [])
                if f.get("severity") == "warning"]

    if not blockers:
        if warnings:
            gaps = "; ".join(
                "[%s] %s" % (f.get("rule_id"), f.get("title"))
                for f in warnings[:8])
            out = {"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "additionalContext": (
                    "提醒：课程交付审计发现 %d 个 warning（无 blocker，已放行）：%s。"
                    "建议修或写豁免理由，详见 /lhg-course-create:course-audit。"
                    % (len(warnings), gaps))}}
            sys.stdout.write(json.dumps(out, ensure_ascii=False))
        return 0

    lines = [
        "交付被 lhg-course-create 硬门拦截：一致性审计发现 %d 个 blocker，"
        "补齐再交付。" % len(blockers),
        "课程目录：%s" % target,
        "",
    ]
    for f in blockers[:10]:
        lines.append("- [%s] %s" % (f.get("rule_id"), f.get("title")))
    if len(blockers) > 10:
        lines.append("…另有 %d 个" % (len(blockers) - 10))
    lines += [
        "",
        "修复方式：按审计报告补齐缺失的讲义/答案后重新交付；",
        "紧急豁免（单次）：LHG_CC_HOOKS_OFF=1 <交付命令>",
    ]
    out = {"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": "\n".join(lines)}}
    sys.stdout.write(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
