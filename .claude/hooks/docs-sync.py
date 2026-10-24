#!/usr/bin/env python3
"""Claude Code PreToolUse hook for documentation sync.

Injects a reminder only for potentially user-facing/config changes,
pointing at .claude/rules/documentation-update.md (fix if wrong; docs
should be high-level; use CodeGraph for internals).
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
    ".git/", ".codegraph/", "node_modules/", ".venv/", "venv/", "data/",
    "dist/", "build/", "coverage/", ".pytest_cache/", ".ruff_cache/",
    "READMEs/assets/", "READMZs/assets/", "uv.lock", "poetry.lock", "package-lock.json", "bun.lock",
)
DOC_SUFFIXES = (".md", ".mdx", ".txt")

# Only remind for changes likely to be user-facing/setup/config
IMPACTFUL_PATTERNS = (
    "docker-compose",
    ".env",
    "pyproject.toml",
    "package.json",
    "apps/",
    "scripts/install",
    "scripts/uninstall",
    "scripts/run",
)

REMINDER = (
    "[docs-sync] Check docs if this change affects setup/features/API/UI or is user-facing. "
    "See .claude/rules/documentation-update.md (fix if wrong, high-level only; use CodeGraph for internals). "
    "No need to update docs for internal refactors/tests. If none needed, say so briefly."
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
    lower = rel_path.lower()
    if lower.endswith(DOC_SUFFIXES):
        return False
    if rel_path.startswith(IGNORED_PREFIXES):
        return False
    # Only remind for impactful paths
    for pat in IMPACTFUL_PATTERNS:
        if pat in lower:
            return True
    return False


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
