#!/usr/bin/env python3
"""Claude Code PreToolUse hook for graphify.

Reminds the agent to use the repo's graphify wrapper (scripts/graphify/graphify.bat
or .sh) instead of the raw `graphify` binary, and to query the knowledge graph for
codebase questions when it exists. Mirrors .opencode/plugins/graphify.js behavior.

Reads the tool-use JSON from stdin and writes the (optionally modified) JSON to stdout.
"""
import json
import os
import sys


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return 0

    tool_name = payload.get("tool_name", "")
    if tool_name != "Bash":
        return 0

    repo_root = os.getcwd()
    if not os.path.exists(os.path.join(repo_root, "graphify-out", "graph.json")):
        return 0

    tool_input = payload.get("tool_input", {})
    command = (tool_input.get("command") or "").strip()

    if command.startswith("graphify ") or command == "graphify":
        reminder = (
            "REMINDER: run graphify through the repo wrapper "
            "(scripts/graphify/graphify.bat on Windows, scripts/graphify/graphify.sh "
            "elsewhere), NEVER the raw `graphify` binary. graphify-out/graph.html is "
            "repo-owned and regenerated only by python scripts/graphify/graphify-html-grouped.py."
        )
        tool_input["command"] = f'echo "{reminder}"; {command}'
        payload["tool_input"] = tool_input
        json.dump(payload, sys.stdout)
        return 0

    # Non-graphify bash command: inject a soft graph reminder once.
    reminder = (
        "[graphify] knowledge graph present at graphify-out/. For focused codebase "
        "questions, run the wrapper query subcommand (scoped subgraph) instead of "
        "grepping raw files; read GRAPH_REPORT.md only for broad context."
    )
    tool_input["command"] = f'echo "{reminder}"; {command}'
    payload["tool_input"] = tool_input
    json.dump(payload, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
