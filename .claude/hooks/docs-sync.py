#!/usr/bin/env python3
"""Claude Code PreToolUse hook for documentation sync.

Injects a reminder the first time the agent edits a source/config file in the
session, pointing at the change -> docs map in .claude/rules/documentation-update.md
so documentation is updated in the same task instead of being requested later.
Mirrors .opencode/plugins/docs-sync.js behavior.

Reads the tool-use JSON from stdin, writes the reminder JSON to stdout.
"""
import hashlib
import json
import os
import sys
import tempfile

TOOLS = {"Edit", "MultiEdit", "NotebookEdit", "Write", "Update"}

# Generated, vendored, or already-documentation paths: no reminder needed.
IGNORED_PREFIXES = (
    ".git/", "graphify-out/", "node_modules/", ".venv/", "venv/", "data/",
    "dist/", "build/", "coverage/", ".pytest_cache/", ".ruff_cache/",
    "READMZs/assets/", "uv.lock", "poetry.lock", "package-lock.json", "bun.lock",
)
DOC_SUFFIXES = (".md", ".mdx", ".txt")

REMINDER = (
    "[docs-sync] Source change detected. Documentation is part of the implementation: "
    "before you finish, apply the change -> docs map in .claude/rules/documentation-update.md "
    "(apps/<module>/README.md for module behavior, root README.md, AGENTS.md, "
    ".claude/CLAUDE.md, READMEs/DOCKER_DEV.md, READMEs/README_INSTALL.md, "
    "READMEs/README_DEVELOPMENT.md, READMEs/README_GITHUB.md, READMEs/AGENTIC_SDLC.md), "
    "and list the docs you updated in your final summary. If none needed changes, say so."
)


def remind_path(cwd: str) -> str:
    key = hashlib.sha256(cwd.encode("utf-8")).hexdigest()[:16]
    return os.path.join(tempfile.gettempdir(), f"ai-job-search-docs-sync-{key}")


def already_reminded(path: str) -> bool:
    try:
        if os.path.exists(path):
            return True
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("reminded\n")
    except OSError:
        return False
    return False


def needs_reminder(rel_path: str) -> bool:
    if not rel_path:
        return False
    rel_path = rel_path.replace("\\", "/")
    if rel_path.lower().endswith(DOC_SUFFIXES):
        return False
    return not rel_path.startswith(IGNORED_PREFIXES)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return 0

    if payload.get("tool_name", "") not in TOOLS:
        return 0

    tool_input = payload.get("tool_input", {}) or {}
    target = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    if not isinstance(target, str):
        return 0

    cwd = os.getcwd()
    rel_path = os.path.relpath(target, cwd) if os.path.isabs(target) else target
    if not needs_reminder(rel_path) or already_reminded(remind_path(cwd)):
        return 0

    json.dump(
        {"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": REMINDER}},
        sys.stdout,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
