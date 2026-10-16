// graphify OpenCode plugin
// Injects a knowledge graph reminder before bash tool calls when the graph exists.
//
// IMPORTANT: keep the reminder string free of backticks and $(...) constructs.
// The hook prepends `echo "<reminder>" && <cmd>` to the user's bash command;
// backticks inside the double-quoted echo trigger bash command substitution,
// which both corrupts tool output and silently executes the very graphify
// command we are only suggesting. Plain words render fine in opencode's TUI.
import { existsSync } from "fs";
import { join } from "path";

export const GraphifyPlugin = async ({ directory }) => {
  let reminded = false;

  return {
    "tool.execute.before": async (input, output) => {
      if (reminded) return;
      if (!existsSync(join(directory, "graphify-out", "graph.json"))) return;

      if (input.tool === "bash") {
        // ';' not '&&' — Windows PowerShell 5.1 rejects '&&' as a statement
        // separator, breaking the first bash command of the session (#1646).
        output.args.command =
          'echo "[graphify] knowledge graph at graphify-out/. For focused questions, run graphify query with your question (scoped subgraph, usually much smaller than GRAPH_REPORT.md) instead of grepping raw files. Read GRAPH_REPORT.md only for broad architecture context." ; ' +
          output.args.command;
        reminded = true;
      }
    },
  };
};

export default {
  id: "graphify",
  async setup(ctx) {
    let reminded = false;
    const directory =
      (ctx && ctx.location && typeof ctx.location.directory === "string" && ctx.location.directory) ||
      (ctx && ctx.location && typeof ctx.location.path === "string" && ctx.location.path) ||
      (ctx && typeof ctx.directory === "string" && ctx.directory) ||
      (typeof process !== "undefined" && typeof process.cwd === "function" ? process.cwd() : ".");

    await ctx.tool.hook("execute.before", async (event) => {
      if (reminded) return;
      if (!event || event.tool !== "shell") return;
      if (!event.input || typeof event.input.command !== "string") return;
      if (!existsSync(join(directory, "graphify-out", "graph.json"))) return;
      // ';' not '&&' — Windows PowerShell 5.1 rejects '&&' as a statement
      // separator, breaking the first bash command of the session (#1646).
      event.input.command =
        'echo "[graphify] knowledge graph at graphify-out/. For focused questions, run graphify query with your question (scoped subgraph, usually much smaller than GRAPH_REPORT.md) instead of grepping raw files. Read GRAPH_REPORT.md only for broad architecture context." ; ' +
        event.input.command;
      reminded = true;
    });
  },
};
