// Command analysis for the test-enforce guardrail.
//
// Detects the test-runner invocations in a shell command, injects the missing
// targets into them and builds the reminder. Imported by
// .opencode/plugins/test-enforce.js and mirrored by
// .claude/hooks/lib/enforce_core.py.
import { existsSync } from "node:fs";
import { join } from "node:path";

export const MARKER = "[test-enforce]";

// A runner path: `./scripts/test.sh`, `scripts\test.bat`, `test.sh`, ...
const RUNNER_PATH = /^(?:\.[\\/])?(?:scripts[\\/])?test[.](?:sh|bat)/i;
// Characters that end a word.
const WORD_BREAKS = new Set([" ", "\t", "\n", "\r", ";", "&", "|", "(", ")", "{", "}", "<", ">"]);
// Characters that end a command and start the next one.
const COMMAND_SEPARATORS = new Set([";", "&", "|", "(", "\n", "\r"]);

// Every runner invocation in the command.
//
// The scan is quote- and command-aware on purpose:
//   - `echo "./scripts/test.sh web"` prints a string and `cat scripts/test.sh`
//     reads a file: neither runs the suite, so neither may be rewritten.
//   - `a && ./scripts/test.sh web && ./scripts/test.sh e2e` has two
//     invocations and both need the missing targets.
export function findRunners(command) {
  const found = [];
  let quote = null;
  let atCommandStart = true;
  let i = 0;
  while (i < command.length) {
    const ch = command[i];
    if (quote) {
      if (ch === quote) quote = null;
      i++;
      continue;
    }
    if (ch === '"' || ch === "'") {
      quote = ch;
      atCommandStart = false;
      i++;
      continue;
    }
    if (COMMAND_SEPARATORS.has(ch)) {
      atCommandStart = true;
      i++;
      continue;
    }
    if (ch === " " || ch === "\t") {
      i++;
      continue;
    }
    if (atCommandStart) {
      const match = RUNNER_PATH.exec(command.slice(i));
      const end = match ? i + match[0].length : -1;
      if (match && (end === command.length || WORD_BREAKS.has(command[end]))) {
        found.push({ start: i, end });
        i = end;
        atCommandStart = false;
        continue;
      }
    }
    atCommandStart = false;
    i++;
  }
  return found;
}

export function findRunner(command) {
  return findRunners(command)[0] || null;
}

function splitArgs(rest) {
  const stop = rest.search(/[;&|\n]/);
  const segment = stop >= 0 ? rest.slice(0, stop) : rest;
  return segment.match(/"[^"]*"|'[^']*'|\S+/g) || [];
}

function isTargetDir(root, token) {
  const clean = token.replace(/^["']|["']$/g, "");
  if (!clean || clean.startsWith("-") || clean === "." || clean === "..") return false;
  if (!root) return false;
  return existsSync(join(root, clean)) || existsSync(join(root, "apps", clean));
}

// Adds `commonlib` and the pending modules to an explicit target list. A runner
// without explicit targets already runs commonlib first, so it is left alone.
export function injectTargets(command, root, pending) {
  const runners = findRunners(command);
  if (!runners.length) return command;
  let out = "";
  let cursor = 0;
  let changed = false;
  for (const runner of runners) {
    const targets = splitArgs(command.slice(runner.end)).filter((t) => isTargetDir(root, t));
    if (!targets.length) continue;
    const names = targets.map((t) => t.replace(/^["']|["']$/g, "").replace(/^apps[\\/]/, "").toLowerCase());
    const wanted = [];
    if (!names.includes("commonlib")) wanted.push("commonlib");
    for (const mod of pending) {
      const key = mod.toLowerCase();
      if (!names.includes(key) && !wanted.some((w) => w.toLowerCase() === key)) wanted.push(mod);
    }
    if (!wanted.length) continue;
    out += command.slice(cursor, runner.end) + " " + wanted.join(" ");
    cursor = runner.end;
    changed = true;
  }
  if (!changed) return command;
  return out + command.slice(cursor);
}

export function buildReminder(modules, global) {
  // `commonlib` is always part of the command, so it is not repeated. Forward
  // slashes keep the reminder safe to echo: a backslash would be read as an
  // escape sequence by shells such as zsh.
  const targets = global ? [] : [...new Set(modules)].filter((m) => m.toLowerCase() !== "commonlib");
  const list = targets.length ? ` commonlib ${targets.join(" ")}` : " commonlib";
  return `${MARKER} Code or test change detected. Run the centralized suite before finishing: ./scripts/test.sh${list} (Linux/Mac) or ./scripts/test.bat${list} (Windows). architecture_test.py only executes under commonlib.`;
}

export function reminderPrefix(reminder) {
  // No double quotes, backticks or $( ) in the reminder: it is echoed by the shell.
  return `echo "${reminder}" ; `;
}

// Session state: the modules changed so far and whether the reminder was shown.
export function createState(root) {
  const pending = new Set();
  let global = false;
  let reminded = false;
  return {
    root,
    pending,
    get global() { return global; },
    record(modules, isGlobal) {
      for (const mod of modules) pending.add(mod);
      global = global || isGlobal;
      reminded = false;
    },
    consumeReminder() {
      if ((!pending.size && !global) || reminded) return null;
      reminded = true;
      return buildReminder([...pending], global);
    },
    clear() {
      pending.clear();
      global = false;
      reminded = true;
    },
  };
}
