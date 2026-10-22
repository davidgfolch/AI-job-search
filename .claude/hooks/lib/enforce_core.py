"""Command analysis for the test-enforce guardrail.

Detects the test-runner invocations in a shell command, injects the missing
targets into them and builds the reminder. Imported by
.claude/hooks/test-enforce.py and mirrored by .opencode/lib/enforce-core.js.
"""
import hashlib
import json
import os
import re
import tempfile

MARKER = "[test-enforce]"

# A runner path: `./scripts/test.sh`, `scripts\test.bat`, `test.sh`, ...
# No `^` anchor: `pattern.match(text, pos)` already anchors at pos, and `^`
# would only match at the real start of the string.
RUNNER_PATH = re.compile(r"(?:\.[\\/])?(?:scripts[\\/])?test[.](?:sh|bat)", re.IGNORECASE)
# Characters that end a word.
WORD_BREAKS = set(" \t\n\r;&|()<>{}")
# Characters that end a command and start the next one.
COMMAND_SEPARATORS = set(";&|(\n\r")


def state_path(root: str) -> str:
    key = hashlib.sha256(root.encode("utf-8")).hexdigest()[:16]
    return os.path.join(tempfile.gettempdir(), f"ai-job-search-test-enforce-{key}")


def load_state(root: str) -> dict:
    try:
        with open(state_path(root), "r", encoding="utf-8") as handle:
            state = json.load(handle)
    except (OSError, json.JSONDecodeError):
        state = {}
    state.setdefault("pending", [])
    state.setdefault("global", False)
    state.setdefault("reminded", False)
    return state


def save_state(root: str, state: dict) -> None:
    try:
        with open(state_path(root), "w", encoding="utf-8") as handle:
            json.dump(state, handle)
    except OSError:
        pass


def find_runners(command: str):
    """Every runner invocation in the command.

    The scan is quote- and command-aware on purpose:
      - `echo "./scripts/test.sh web"` prints a string and `cat scripts/test.sh`
        reads a file: neither runs the suite, so neither may be rewritten.
      - `a && ./scripts/test.sh web && ./scripts/test.sh e2e` has two
        invocations and both need the missing targets.
    """
    found = []
    quote = None
    at_command_start = True
    index = 0
    length = len(command)
    while index < length:
        char = command[index]
        if quote:
            if char == quote:
                quote = None
            index += 1
            continue
        if char in "\"'":
            quote = char
            at_command_start = False
            index += 1
            continue
        if char in COMMAND_SEPARATORS:
            at_command_start = True
            index += 1
            continue
        if char in " \t":
            index += 1
            continue
        if at_command_start:
            match = RUNNER_PATH.match(command, index)
            end = match.end() if match else -1
            if match and (end == length or command[end] in WORD_BREAKS):
                found.append((index, end))
                index = end
                at_command_start = False
                continue
        at_command_start = False
        index += 1
    return found


def find_runner(command: str):
    runners = find_runners(command)
    return runners[0] if runners else None


def split_args(rest: str):
    stop = re.search(r"[;&|\n]", rest)
    segment = rest[:stop.start()] if stop else rest
    return re.findall(r"\"[^\"]*\"|'[^']*'|\S+", segment)


def is_target_dir(root: str, token: str) -> bool:
    clean = token.strip("\"'")
    if not clean or clean.startswith("-") or clean in (".", ".."):
        return False
    return os.path.isdir(os.path.join(root, clean)) or os.path.isdir(os.path.join(root, "apps", clean))


def inject_targets(command: str, root: str, pending) -> str:
    """Add `commonlib` and the pending modules to an explicit target list.

    A runner without explicit targets already runs commonlib first, so it is
    left alone. Every runner invocation in the command is handled.
    """
    runners = find_runners(command)
    if not runners:
        return command
    out = []
    cursor = 0
    changed = False
    for _start, end in runners:
        targets = [t for t in split_args(command[end:]) if is_target_dir(root, t)]
        if not targets:
            continue
        names = [t.strip("\"'").replace("\\", "/").split("/")[-1].lower() for t in targets]
        wanted = [] if "commonlib" in names else ["commonlib"]
        for module in pending:
            key = module.lower()
            if key not in names and key not in [w.lower() for w in wanted]:
                wanted.append(module)
        if not wanted:
            continue
        out.append(command[cursor:end])
        out.append(" " + " ".join(wanted))
        cursor = end
        changed = True
    if not changed:
        return command
    out.append(command[cursor:])
    return "".join(out)


def build_reminder(modules, is_global: bool) -> str:
    # `commonlib` is always part of the command, so it is not repeated. Forward
    # slashes keep the reminder safe to echo: a backslash would be read as an
    # escape sequence by shells such as zsh.
    targets = [] if is_global else [m for m in dict.fromkeys(modules) if m.lower() != "commonlib"]
    targets = " commonlib " + " ".join(targets) if targets else " commonlib"
    return (
        f"{MARKER} Code or test change detected. Run the centralized suite before finishing: "
        f"./scripts/test.sh{targets} (Linux/Mac) or ./scripts/test.bat{targets} (Windows). "
        "architecture_test.py only executes under commonlib."
    )
