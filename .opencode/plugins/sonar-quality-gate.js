// SonarQube quality-gate OpenCode plugin
// Forces a passing local SonarQube scan before any git push.
import { execSync } from "node:child_process";

function rootDir() {
  return process.cwd();
}

export const SonarQualityGatePlugin = async () => {
  return {
    "tool.execute.before": async (input, output) => {
      if (input.tool !== "bash") return;
      const command = (output.args || {}).command;
      if (!command || !/\bgit\b.*\bpush\b/.test(command)) return;
      if (command.includes("SKIP_SONAR=1")) return;
      try {
        execSync("sh scripts/sonar.sh scan", { stdio: "inherit", cwd: rootDir() });
      } catch (error) {
        throw new Error(
          "BLOCKED by SonarQube quality gate: local scan failed. " +
            "Run scripts/sonar.sh scan, fix the reported issues, then retry the push.",
        );
      }
      output.args.command = "SKIP_SONAR=1 " + command;
    },
  };
};

export default {
  id: "sonar-quality-gate",
  async setup(ctx) {
    await ctx.tool.hook("execute.before", async (event) => {
      if (event.tool !== "shell") return;
      const command = (event.input || {}).command;
      if (!command || !/\bgit\b.*\bpush\b/.test(command)) return;
      if (command.includes("SKIP_SONAR=1")) return;
      try {
        execSync("sh scripts/sonar.sh scan", { stdio: "inherit", cwd: rootDir() });
      } catch (error) {
        throw new Error("BLOCKED by SonarQube quality gate: local scan failed.");
      }
      event.input.command = "SKIP_SONAR=1 " + command;
    });
  },
};