#!/usr/bin/env python3
"""Claude Code PreToolUse hook: require a passing local SonarQube gate before push."""
import hashlib
import json
import os
import re
import sys
import datetime
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
MARKER = ROOT / ".sonar-gate-passed"
STALE_MINUTES = 30


def current_state():
    head = subprocess_output(["git", "rev-parse", "HEAD"]).strip()
    status = subprocess_output(["git", "status", "--porcelain"], as_list=False)
    return {
        "head": head,
        "status_sha256": hashlib.sha256(status.encode("utf-8")).hexdigest(),
    }


def subprocess_output(cmd, as_list=True):
    import subprocess
    if as_list:
        return subprocess.check_output(cmd, cwd=ROOT, text=True)
    return subprocess.check_output(cmd, cwd=ROOT, text=True)


def is_git_push(command):
    if not isinstance(command, str):
        return False
    if not re.search(r"\bgit\b", command):
        return False
    return bool(re.search(r"\bpush\b", command))


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return 0
    command = payload.get("tool_input", {}).get("command", "")
    if payload.get("tool_name") != "Bash" or not is_git_push(command):
        return 0

    if not MARKER.exists():
        block("No local SonarQube quality-gate marker found. Run scripts/sonar.sh scan (or .bat) and fix all findings before pushing.")
        return 2

    try:
        marker = json.loads(MARKER.read_text())
    except (json.JSONDecodeError, OSError):
        block("SonarQube marker is corrupt. Re-run scripts/sonar.sh scan.")
        return 2

    state = current_state()
    if marker.get("head") != state["head"]:
        block("SonarQube marker does not match current HEAD. Re-run scripts/sonar.sh scan before pushing.")
        return 2
    if marker.get("status_sha256") != state["status_sha256"]:
        block("Working-tree changes were detected after the last SonarQube scan. Re-run scripts/sonar.sh scan before pushing.")
        return 2

    timestamp = marker.get("timestamp_utc", "")
    try:
        parsed = datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        age = datetime.datetime.now(datetime.timezone.utc) - parsed
        if age.total_seconds() > STALE_MINUTES * 60:
            block(f"Last SonarQube scan is older than {STALE_MINUTES} minutes. Re-run scripts/sonar.sh scan before pushing.")
            return 2
    except (ValueError, TypeError):
        block("SonarQube marker timestamp is invalid. Re-run scripts/sonar.sh scan.")
        return 2

    return 0


def block(message):
    print("BLOCKED by .claude/hooks/sonar-quality-gate.py: " + message, file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
