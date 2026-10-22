// test-enforce OpenCode plugin
// Guarantees the centralized test suite runs after a code or test change.
//
// apps/commonlib/commonlib/test/architecture_test.py is the only place the repo's
// architecture rules are enforced (file length, layering, test naming, sibling
// tests, bare print, console= contract). It lives in commonlib, so it executes
// only when commonlib is one of the modules passed to scripts/test.sh.
//
// Two mechanisms:
//   1. Injection: a `scripts/test.sh` / `scripts/test.bat` invocation gets
//      `commonlib` plus every module changed since the last run added to its
//      target list, so the architecture tests always execute.
//   2. Reminder: after an edit that touches code or tests, the next shell
//      command carries a reminder with the exact command to run.
//
// Mirrors .claude/hooks/test-enforce.py behavior; the canonical policy lives in
// .claude/rules/test-enforcement.md.
import { buildReminder, createState, findRunner, injectTargets, reminderPrefix } from "../lib/enforce-core.js";
import { classify, relativize, toRoot } from "../lib/enforce-paths.js";

// The shell tool is exposed as "shell" by current opencode versions and "bash"
// by older ones, so both are accepted.
const SHELL_TOOLS = new Set(["shell", "bash"]);
const EDIT_TOOLS = new Set(["edit", "write", "patch", "multiedit"]);

// The hook payload: { tool, sessionID, agent, messageID, id, input }.
// `input` is the tool argument object and is mutable, so rewriting
// `input.command` changes the command that actually runs.
function createHooks(root) {
  const state = createState(root);
  return {
    "tool.execute.before": async (event) => {
      if (!event || !event.tool) return;
      const args = event.input || {};
      if (EDIT_TOOLS.has(event.tool)) {
        const hit = classify(relativize(args.path || args.filePath || args.file, root));
        if (hit) state.record(hit.modules, hit.global);
        return;
      }
      if (!SHELL_TOOLS.has(event.tool) || typeof args.command !== "string" || !args.command) return;
      if (findRunner(args.command)) {
        args.command = injectTargets(args.command, root, [...state.pending]);
        state.clear();
        return;
      }
      const reminder = state.consumeReminder();
      if (reminder && !args.command.includes("[test-enforce]")) args.command = reminderPrefix(reminder) + args.command;
    },
  };
}

// Named export kept for the documented plugin API (a module that exports one or
// more plugin functions). The default export below is the shape this opencode
// version loads.
export const TestEnforcePlugin = async () => createHooks(toRoot(process.cwd()));

export default {
  id: "test-enforce",
  async setup(ctx) {
    const root = toRoot((ctx && ctx.location && ctx.location.directory) || process.cwd());
    const hooks = createHooks(root);
    await ctx.tool.hook("execute.before", hooks["tool.execute.before"]);
  },
};
