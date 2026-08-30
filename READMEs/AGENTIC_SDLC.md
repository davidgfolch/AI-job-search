# Agentic SDLC

This document centralizes how agentic coding assistants (opencode, Claude Code) work with this repository: where their configuration lives, the skills they expose, and the workflows they drive (knowledge-graph queries, Dependabot processing, and more).

## Agent Homes

Agentic configuration and rules are consolidated under `.claude/` as the canonical home.

| Directory | Purpose |
|-----------|---------|
| `.claude/skills/` | Canonical home for all agent skills |
| `.claude/rules/` | Shared rule files (e.g. `architecture-guidelines.md`) |
| `.claude/CLAUDE.md` | Agent guidance for Claude Code (repo overview, build/test commands, code style, graphify rules) |
| `.claude/settings.json` | Project-shared Claude Code settings (hooks) |
| `.claude/settings.local.json` | Local Claude Code permissions (not committed) |
| `.opencode/` | opencode-specific config only: `plugins/graphify.js`, `opencode.json`, and `plans/`. opencode plugins must live here (`issue #8158`) |

> **Note:** `.agent/` is retired. Skills and rules that previously lived in `.agent/` and the now-consolidated `.opencode/skills/` all live under `.claude/skills/` / `.claude/rules/` today.

## Skills

All agent skills live in `.claude/skills/`. Core ones:

- **`skill-builder`** — Creates new agent skills. Ask the agent to "create a new skill named [skill-name]".
- **`e2e-implementer`** — Creates/reruns Playwright E2E tests in `apps/e2e`.
- **`test-implementer`** — Implements unit tests following valid architecture and best practices.
- **`graphify`** — Queries the repository knowledge graph (`/graphify`, `query`, `path`, `explain`).
- **`graphify-dev`** — Changes/improves graphify functionality. MANDATORY before editing anything graphify-related; never modify the uv-installed graphify package.
- **`version-bumper`** — Bumps the version of any `apps/*` module following semver.
- **`dependabot-agent`** — Processes open GitHub Dependabot PRs.
- **`scrapling-implementer`** — Scrapling library usage (fetching, parsing, spiders).
- **`view-backend-logs`** — How to view backend logs using docker-compose.

## graphify (knowledge graph)

The project maintains a knowledge graph at `graphify-out/` (god nodes, community structure, cross-file relationships).

**Always run graphify through the wrapper** — `scripts/graphify/graphify.bat` (Windows) or `scripts/graphify/graphify.sh` (Linux/Mac) — **never the raw `graphify` binary**. The wrapper owns the full pipeline (no args = rebuild, `--clean`, `--module <name>`) and delegates `query`/`path`/`explain` to the CLI; mutating subcommands (`update`, `cluster-only`, `add`, `export`, `extract`, `merge-graphs`, URLs) are delegated and then re-run the repo HTML generator.

`graphify-out/graph.html` is **repo-owned**: generated ONLY by `python scripts/graphify/graphify-html-grouped.py`. Never regenerate it with upstream CLI commands.

Rules:
- For codebase questions, first run the wrapper `query` subcommand when `graphify-out/graph.json` exists (scoped subgraph, usually much smaller than `GRAPH_REPORT.md`).
- Use `path` for relationships, `explain` for focused concepts.
- Dirty `graphify-out/` files are expected after hooks/incremental updates; not a reason to skip graphify.
- If `graphify-out/wiki/index.md` exists, use it for broad navigation.
- Read `graphify-out/GRAPH_REPORT.md` only for broad architecture review.
- After modifying code, run the wrapper `update` subcommand to keep the graph current (AST-only, no API cost).

## Dependabot PR workflow

The `dependabot-agent` skill processes open Dependabot PRs (they target `staging`; validated batches reach `master` only through the persistent `staging → master` promotion PR). The agent:

1. Runs the TDD pipeline for the affected module.
2. **Builds and runs** the affected Docker services in an isolated sandbox (`scripts/test-sandbox.*`, project `dependabot-test`) that renames containers, remaps ports, disables autodiscovery, clones the live `jobs` DB, and checks logs for errors.
3. Aborts the whole process on any build/start/log error.
4. Fixes failures and pushes so auto-merge can proceed.

Requires Docker and the GitHub CLI (`gh`, see [README_INSTALL.md](README_INSTALL.md)).

**Usage:** ask the agent to "process the open dependabot PRs" (optionally scoped to a module).

## Related Documentation

- **Installation Guide**: [README_INSTALL.md](README_INSTALL.md)
- **Docker Development**: [DOCKER_DEV.md](DOCKER_DEV.md)
- **Contribution Guide**: [README_CONTRIBUTE.md](README_CONTRIBUTE.md)
- **GitHub Workflow**: [README_GITHUB.md](README_GITHUB.md)
