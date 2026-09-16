#!/usr/bin/env python3
"""Claude Code PreToolUse hook for docker --build.

Silently injects --build into `docker compose up` commands so containers always
reflect current Dockerfiles, dependency manifests, and baked .env. Image-only
services (mysql, mongo, ollama, prometheus, grafana) get a harmless no-op build.

Reading tool-use JSON from stdin, writing the modified JSON to stdout.
Mirrors .opencode/plugins/docker-build.js behavior.
"""
import json
import re
import sys

# Subcommands that are NOT `up` — never inject --build into them.
OTHER_SUBCOMMANDS = {
    "attach", "build", "config", "convert", "cp", "create", "diff", "down",
    "events", "exec", "help", "images", "inspect", "kill", "logs", "ls",
    "pause", "port", "ps", "pull", "push", "rename", "restart", "rm", "run",
    "start", "stats", "stop", "top", "unpause", "update", "version", "wait",
}

# docker compose/docker-compose global flags take optional values (e.g. -p name),
# so the segment between `compose` and `up` may contain anything except shell
# separators and quotes. A stop in quotes avoids rewriting `exec ... "up"`.
MATCH = re.compile(
    r"\b(?:docker(?:-|\s+)compose)((?:[^\&|;`\"']|$)*?)\bup\b"
)

SKIP = re.compile(r"--(?:no-)?build\b")


def is_up_command(text: str) -> re.Match | None:
    match = MATCH.search(text)
    if not match:
        return None
    segment = match.group(1)
    if any(re.search(rf"\b{w}\b", segment) for w in OTHER_SUBCOMMANDS):
        return None
    return match


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return 0

    tool_name = payload.get("tool_name", "")
    if tool_name != "Bash":
        return 0

    tool_input = payload.get("tool_input", {})
    command = (tool_input.get("command") or "").strip()
    if not command or SKIP.search(command):
        json.dump(payload, sys.stdout)
        return 0

    match = is_up_command(command)
    if not match:
        json.dump(payload, sys.stdout)
        return 0

    end = match.end()
    tool_input["command"] = command[:end] + " --build" + command[end:]
    payload["tool_input"] = tool_input
    json.dump(payload, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())