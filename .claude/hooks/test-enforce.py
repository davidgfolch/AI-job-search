#!/usr/bin/env python3
"""Claude Code PreToolUse hook: enforce the centralized test suite.

apps/commonlib/commonlib/test/architecture_test.py is the only place the repo's
architecture rules are enforced (file length, layering, test naming, sibling
tests, bare print, console= contract). It lives in commonlib, so it executes
only when commonlib is one of the modules passed to scripts/test.sh.

Two mechanisms:
  1. Injection: a `scripts/test.sh` / `scripts/test.bat` invocation gets
     `commonlib` plus every module changed since the last run added to its
     target list, so the architecture tests always execute.
  2. Reminder: after an edit that touches code or tests, the next Bash call
     carries a reminder with the exact command to run.

Mirrors .opencode/plugins/test-enforce.js behavior; the canonical policy lives
in .claude/rules/test-enforcement.md.

Reads the tool-use JSON from stdin and writes the (possibly modified) JSON to
stdout.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

from enforce_core import build_reminder, find_runner, inject_targets, load_state, save_state
from enforce_paths import classify, relativize

EDIT_TOOLS = {"Edit", "MultiEdit", "Write", "NotebookEdit", "Update"}


def handle_edit(payload: dict, root: str) -> int:
    tool_input = payload.get("tool_input", {}) or {}
    target = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    if not isinstance(target, str):
        return 0
    hit = classify(relativize(target, root))
    if not hit:
        return 0
    modules, is_global = hit
    state = load_state(root)
    for module in modules:
        if module not in state["pending"]:
            state["pending"].append(module)
    state["global"] = state["global"] or is_global
    state["reminded"] = False
    save_state(root, state)
    context = build_reminder(state["pending"], state["global"])
    json.dump({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": context}}, sys.stdout)
    return 0


def handle_bash(payload: dict, root: str) -> int:
    tool_input = payload.get("tool_input", {}) or {}
    command = tool_input.get("command") or ""
    if not isinstance(command, str) or not command.strip():
        json.dump(payload, sys.stdout)
        return 0
    state = load_state(root)
    if find_runner(command):
        tool_input["command"] = inject_targets(command, root, state["pending"])
        state["pending"], state["global"], state["reminded"] = [], False, True
        save_state(root, state)
        payload["tool_input"] = tool_input
        json.dump(payload, sys.stdout)
        return 0
    pending = state["pending"]
    if (pending or state["global"]) and not state["reminded"]:
        state["reminded"] = True
        save_state(root, state)
        reminder = build_reminder(pending, state["global"]).replace('"', "'")
        tool_input["command"] = f'echo "{reminder}" ; ' + command
        payload["tool_input"] = tool_input
    json.dump(payload, sys.stdout)
    return 0


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return 0
    root = os.getcwd()
    tool_name = payload.get("tool_name", "")
    if tool_name in EDIT_TOOLS:
        return handle_edit(payload, root)
    if tool_name == "Bash":
        return handle_bash(payload, root)
    json.dump(payload, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
