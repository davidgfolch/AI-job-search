// docs-sync OpenCode plugin
// Nudges the agent to update documentation in the same task as the code change.
//
// It flags edits/writes/patches that touch source or config files (not markdown,
// not generated/vendored paths) and, on the next bash call of the session, prints
// the change -> docs map reminder once. Silent when no such edit happened.
// Mirrors .claude/hooks/docs-sync.py behavior; the canonical map lives in
// .claude/rules/documentation-update.md.
//
// IMPORTANT: keep the reminder string free of backticks and $(...) constructs.
// The reminder is printed with `echo "<reminder>"`, where backticks would trigger
// shell command substitution.
const EDIT_TOOLS = new Set(["edit", "write", "patch", "multiedit"]);

const IGNORED_PREFIXES = [
  ".git/",
  "graphify-out/",
  "node_modules/",
  ".venv/",
  "venv/",
  "data/",
  "dist/",
  "build/",
  "coverage/",
  ".pytest_cache/",
  ".ruff_cache/",
  "READMEs/assets/",
];
const IGNORED_FILES = ["uv.lock", "poetry.lock", "package-lock.json", "bun.lock"];
const DOC_SUFFIXES = [".md", ".mdx", ".txt"];

const REMINDER =
  'echo "[docs-sync] source change detected: update docs in this same task. Apply the change to docs map in .claude/rules/documentation-update.md (apps/<module>/README.md, root README.md, AGENTS.md, .claude/CLAUDE.md, READMEs/DOCKER_DEV.md, READMEs/README_INSTALL.md, READMEs/README_DEVELOPMENT.md, READMEs/README_GITHUB.md, READMEs/AGENTIC_SDLC.md) and list updated docs in your final summary; if none needed, say so." ; ';

function needsReminder(filePath) {
  if (!filePath) return false;
  const p = filePath.replace(/\\/g, "/");
  const lower = p.toLowerCase();
  if (DOC_SUFFIXES.some((ext) => lower.endsWith(ext))) return false;
  if (IGNORED_FILES.some((f) => lower.endsWith("/" + f) || lower === f)) return false;
  const marker = p.lastIndexOf("/");
  const tail = marker >= 0 ? p.slice(marker + 1) : p;
  if (IGNORED_PREFIXES.includes(tail)) return false;
  const segments = p.split("/");
  return !IGNORED_PREFIXES.some((prefix) => {
    const parts = prefix.split("/");
    return parts.every((part, i) => segments[i] === part);
  });
}

export const DocsSyncPlugin = async () => {
  let codeChanged = false;
  let reminded = false;

  return {
    "tool.execute.before": async (input, output) => {
      if (EDIT_TOOLS.has(input.tool)) {
        const args = output.args || {};
        if (needsReminder(args.filePath || args.path || args.file)) codeChanged = true;
        return;
      }
      if (input.tool !== "bash" || reminded || !codeChanged) return;
      if (!output.args || !output.args.command) return;
      // ';' not '&&' - Windows PowerShell 5.1 rejects '&&' as a statement separator.
      output.args.command = REMINDER + output.args.command;
      reminded = true;
    },
  };
};
