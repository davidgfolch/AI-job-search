# Agentic SDLC

This document centralizes how agentic coding assistants (opencode, Claude Code) work with this repository: where their configuration lives, the skills they expose, and the workflows they drive (knowledge-graph queries, Dependabot processing, and more).

## Agent Homes

Agentic configuration and rules are consolidated under `.claude/` as the canonical home.

| Directory | Purpose |
|-----------|---------|
| `.claude/skills/` | Canonical home for all agent skills |
| `.claude/rules/` | Shared rule files (`architecture-guidelines.md`, `docker-build.md`, `documentation-update.md`, `db-mutation-permission.md`); opencode loads them all via `instructions` in `.opencode/opencode.json` |
| `.claude/hooks/` | Claude Code `PreToolUse` hooks (`docker-build.py`, `docs-sync.py`, `db-mutation.py`) |
| `.claude/CLAUDE.md` | Agent guidance for Claude Code (repo overview, build/test commands, code style, graphify rules) |
| `.claude/settings.json` | Project-shared Claude Code settings (hooks) |
| `.claude/settings.local.json` | Local Claude Code permissions (not committed) |
| `.opencode/` | opencode-specific config only: `plugins/graphify.js`, `plugins/docker-build.js`, `plugins/docs-sync.js`, `plugins/db-mutation.js`, `opencode.json`, and `plans/`. opencode plugins must live here (`issue #8158`) |

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
- **`gh-actions-debug`** — Debugs GitHub Actions / Dependabot run failures with `gh`.
- **`scrapling-implementer`** — Scrapling library usage (fetching, parsing, spiders).
- **`crawlee-page-analyst`** — Uses Crawlee to analyze a source page after a site/DOM change and produce scrapper-change requirements before editing selectors.
- **`view-backend-logs`** — How to view backend logs using docker-compose.

## Required Tools

Agentic workflows require **Docker** and the **GitHub CLI (`gh`, see [README_INSTALL.md](README_INSTALL.md))**. `gh` is used by `dependabot-agent` (processing Dependabot PRs) and `gh-actions-debug` (inspecting workflow/Dependabot run logs, which the web UI hides behind a write-access link). **Crawlee** (`uv tool install "crawlee[all]"`, installed automatically by `scripts/install.*`, see [README_INSTALL.md](README_INSTALL.md)) is used by `crawlee-page-analyst` to analyze source-page changes.

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

## Crawlee (source-page change analysis)

When an `apps/scrapper` change is required because a source page changed (DOM redesign, new URL pattern, moved to client-side rendering), the `crawlee-page-analyst` skill is the mandatory first step: fetch the live page with Crawlee, diff the DOM against the selectors the scrapper uses, and produce selector-level requirements **before** editing any scrapper code. The analysis decides which fields broke, which crawler class fits (static vs JS-rendered), and whether the fix affects the Selenium path, the Scrapling path, or both. Crawlee is installed as a host tool (`uv tool install "crawlee[all]"`, run automatically by `scripts/install.sh` / `scripts/install.bat`); see [README_INSTALL.md](README_INSTALL.md) and the skill at `.claude/skills/crawlee-page-analyst/SKILL.md`.

## Documentation Sync (automatic, mandatory)

Documentation is updated **in the same session** as every plan implementation, feature, fix, refactor, config change, or dependency bump — it is never a follow-up task, and it is never left for the user to ask for.

The workflow is defined once in `.claude/rules/documentation-update.md` (an always-on rule, loaded by opencode through `instructions` and by any harness that reads `.claude/rules/`), and it is reinforced automatically by:

| Mechanism | Harness | What it does |
|-----------|---------|--------------|
| `.claude/rules/documentation-update.md` | all | Canonical rule: when the doc sync applies, the change → docs map, and the definition-of-done checklist |
| `.claude/hooks/docs-sync.py` | Claude Code (`PreToolUse` on `Edit`/`MultiEdit`/`Write`/`NotebookEdit`) | Injects a reminder the first time a source/config file is edited in the session |
| `.opencode/plugins/docs-sync.js` | opencode | Tracks source edits and prints the same reminder once on the next bash call |

Every task ends with the same five steps: pick the doc-map rows that match the change, open each listed doc, fix only what became inaccurate, keep snippets copy-pasteable, and report the updated docs in the final summary (or state that none were needed).

Rows of the map worth remembering: module behavior → `apps/<module>/README.md`; new/removed module → root `README.md`, `AGENTS.md`, `.claude/CLAUDE.md`; env var → root `README.md` (Settings); compose service/profile/port → `READMEs/DOCKER_DEV.md`; build/test/install command → `AGENTS.md`, `.claude/CLAUDE.md`, `READMEs/README_DEVELOPMENT.md`; new host tool → `READMEs/README_INSTALL.md`; API/DB schema → `apps/backend/README.md`; user-facing UI → root `README.md` (Features/Screenshots); CI/Dependabot → `READMEs/README_GITHUB.md`; skill/rule/hook/plugin → this file plus the Skills lists; plan implementation → the plan file (`Status:` + outcome) and `READMZs/TODO.md`.

`graphify-out/` is generated output: refresh it with the wrapper (`scripts\graphify\graphify.bat update .`) after code changes, but never hand-edit it and never count it as documentation.

## Database changes require user permission (enforced guardrail)

The `jobs` MySQL database is **live production data** — scraping, enrichment, applications, and manual curation write to it continuously. A data or schema mutation is therefore never the agent's own initiative: measure the current state with read-only SQL, state the exact statement and the expected row count, then wait for the user to say yes. The policy is defined once in `.claude/rules/db-mutation-permission.md` and is **enforced in the tool call itself**, so it does not depend on the agent remembering it:

| Mechanism | Harness | What it does |
|-----------|---------|--------------|
| `.claude/rules/db-mutation-permission.md` | all | Canonical policy: what is blocked, what stays allowed, and how to ask |
| `.claude/hooks/db-mutation.py` | Claude Code (`PreToolUse` on `Bash`) | Exits 2 and denies the call, printing the reason and the remediation on stderr |
| `.opencode/plugins/db-mutation.js` | opencode | Throws from `tool.execute.before`, aborting the `bash` call with the same message |

Both are registered automatically: the hook in `.claude/settings.json` (`PreToolUse` → `Bash`), the plugin in the `plugin` array of `.opencode/opencode.json`. Both mirror each other and share the same detection logic, verified by an identical 31-case allow/block matrix.

What it blocks: a database client (`mysql`, `mariadb`, `psql`, `mongosh`, `sqlite3`, `redis-cli`, …) combined with a mutating statement (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `TRUNCATE`, `ALTER`, `CREATE`, `GRANT`, `CALL`, `LOAD DATA`, `… INTO OUTFILE`), a `.sql` file piped or sourced into a client (contents are not reviewable), mongo mutators (`drop`, `updateMany`, `deleteMany`, `bulkWrite`), redis writes (`SET`, `DEL`, `FLUSHALL`), and data-volume destruction (`docker compose down -v`, `docker volume rm`, `docker system prune --volumes`).

What stays allowed, and is expected in normal work: `SELECT`, `SHOW`, `DESCRIBE`, `EXPLAIN`, `COUNT`, `WITH … SELECT`, `SELECT ROW_COUNT()`, reading container logs and `.env`, and `docker compose restart/up/logs/ps`.

**Approving a mutation.** Only after the user approves that exact statement, re-run it with the `AI_DB_WRITE_APPROVED` token in the command; the guardrail then passes it through:

```bash
AI_DB_WRITE_APPROVED=1 docker exec ai-job-search-mysql mysql -uroot -prootPass jobs -e "UPDATE ..."
```

```powershell
$env:AI_DB_WRITE_APPROVED=1; docker exec ai-job-search-mysql mysql -uroot -prootPass jobs -e "UPDATE ..."
```

Adding the token is itself a permission decision: never add it to a statement the user has not approved, and re-confirm when the scope grows (approved for 100 rows is not approval for 6000).

Honest limits: the guardrail matches clients, SQL keywords, and destructive volume commands by pattern. It cannot see inside an arbitrary script that builds SQL dynamically, and it cannot verify that the user actually consented. When a mutation is genuinely warranted and runs with the token, say so explicitly in the summary.

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
