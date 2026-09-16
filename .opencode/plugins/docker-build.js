// docker-build OpenCode plugin
// Silently injects --build into `docker compose up` commands so containers always
// reflect current Dockerfiles, dependency manifests, and baked .env. Image-only
// services (mysql, mongo, ollama, prometheus, grafana) get a harmless no-op build.
// Mirrors .claude/hooks/docker-build.py behavior.
const OTHER_SUBCOMMANDS = new Set([
  "attach", "build", "config", "convert", "cp", "create", "diff", "down",
  "events", "exec", "help", "images", "inspect", "kill", "logs", "ls",
  "pause", "port", "ps", "pull", "push", "rename", "restart", "rm", "run",
  "start", "stats", "stop", "top", "unpause", "update", "version", "wait",
]);

const MATCH = /\b(?:docker(?:-|\s+)compose)((?:[^&|;`"']|$)*?)\bup\b/;
const SKIP = /--(?:no-)?build\b/;

function injectBuild(command) {
  if (!command || SKIP.test(command)) return command;
  const match = MATCH.exec(command);
  if (!match) return command;
  const segment = match[1];
  for (const word of OTHER_SUBCOMMANDS) {
    if (new RegExp(`\\b${word}\\b`).test(segment)) return command;
  }
  const end = match.index + match[0].length;
  return command.slice(0, end) + " --build" + command.slice(end);
}

export const DockerBuildPlugin = async () => {
  return {
    "tool.execute.before": async (input, output) => {
      if (input.tool !== "bash") return;
      output.args.command = injectBuild(output.args.command);
    },
  };
};