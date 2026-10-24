// docs-sync OpenCode plugin
// Nudges the agent to check docs only for impactful changes
// (fix if wrong; high-level only; use CodeGraph for internals).
// Mirrors .claude/hooks/docs-sync.py behavior; the canonical policy lives in
// .claude/rules/documentation-update.md.

const EDIT_TOOLS = new Set(["edit", "write", "patch", "multiedit"]);

const IGNORED_PREFIXES = [
  ".git/",
  ".codegraph/",
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
  "READMZs/assets/",
];
const IGNORED_FILES = ["uv.lock", "poetry.lock", "package-lock.json", "bun.lock"];
const DOC_SUFFIXES = [".md", ".mdx", ".txt"];

const IMPACTFUL_PATTERNS = [
  "docker-compose",
  ".env",
  "pyproject.toml",
  "package.json",
  "apps/",
  "scripts/install",
  "scripts/uninstall",
  "scripts/run",
];

const REMINDER =
  'echo "[docs-sync] Check docs if this change affects setup/features/API/UI or is user-facing. See .claude/rules/documentation-update.md (fix if wrong, high-level only; use CodeGraph for internals). No need to update docs for internal refactors/tests. If none needed, say so briefly." ; ';

// Idempotency guard
const MARKER = "[docs-sync]";

function shouldPrepend(command) {
  return typeof command === "string" && command.length > 0 && !command.includes(MARKER);
}

function needsReminder(filePath) {
  if (!filePath) return false;
  const p = filePath.replace(/\\/g, "/");
  const lower = p.toLowerCase();
  if (DOC_SUFFIXES.some((ext) => lower.endsWith(ext))) return false;
  if (IGNORED_FILES.some((f) => lower.endsWith("/" + f) || lower === f)) return false;
  // Check ignored prefixes
  const segments = p.split("/");
  for (const prefix of IGNORED_PREFIXES) {
    const parts = prefix.split("/").filter(Boolean);
    if (parts.length === 0) continue;
    let match = true;
    for (let i = 0; i < parts.length; i++) {
      if (segments[i] !== parts[i]) { match = false; break; }
    }
    if (match) return false;
  }
  // Only remind for impactful patterns
  for (const pat of IMPACTFUL_PATTERNS) {
    if (lower.includes(pat)) return true;
  }
  return false;
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
      if (!output.args || !shouldPrepend(output.args.command)) return;
      output.args.command = REMINDER + output.args.command;
      reminded = true;
    },
  };
};
export default {
  id: "docs-sync",
  async setup(ctx) {
    let codeChanged = false;
    let reminded = false;

    await ctx.tool.hook("execute.before", async (event) => {
      if (!event || !event.tool) return;
      if (EDIT_TOOLS.has(event.tool)) {
        const args = (event.input || {});
        if (needsReminder(args.filePath || args.path || args.file)) codeChanged = true;
        return;
      }
      if (event.tool !== "shell" || reminded || !codeChanged) return;
      if (!event.input || !shouldPrepend(event.input.command)) return;
      event.input.command = REMINDER + event.input.command;
      reminded = true;
    });
  },
};
