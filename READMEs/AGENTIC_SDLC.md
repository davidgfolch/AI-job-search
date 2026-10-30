# Agentic SDLC

This document centralizes how agentic coding assistants (opencode, Claude Code) work with this repository: where their configuration lives, the skills they expose, and the workflows they drive (CodeGraph exploration, Dependabot processing, and more).

## Agent Homes

Agentic configuration and rules are consolidated under `.claude/` as the canonical home.

| Directory | Purpose |
|-----------|---------|
| `.claude/skills/` | Canonical home for all agent skills |
| `.claude/rules/` | Shared rule files (`architecture-guidelines.md`, `docker-build.md`, `documentation-update.md`, `db-mutation-permission.md`, `test-enforcement.md`); opencode loads them all via `instructions` in `.opencode/opencode.json` |
| `.claude/hooks/` | Claude Code `PreToolUse` hooks (`docker-build.py`, `docs-sync.py`, `db-mutation.py`, `test-enforce.py`) and their shared logic (`lib/`) |
| `.claude/CLAUDE.md` | Agent guidance for Claude Code (repo overview, build/test commands, code style) |
| `.claude/settings.json` | Project-shared Claude Code settings (hooks) |
| `.claude/settings.local.json` | Local Claude Code permissions (not committed) |
| `.opencode/` | opencode-specific config only: `plugins/docker-build.js`, `plugins/docs-sync.js`, `plugins/db-mutation.js`, `plugins/test-enforce.js`, the shared plugin logic in `lib/`, `opencode.json`, and `plans/`. opencode plugins must live here (`issue #8158`) |

> **Note:** `.agent/` is retired. Skills and rules that previously lived in `.agent/` and the now-consolidated `.opencode/skills/` all live under `.claude/skills/` / `.claude/rules/` today.

## Skills

All agent skills live in `.claude/skills/`. Core ones:

- **`skill-builder`** — Creates new agent skills. Ask the agent to "create a new skill named [skill-name]".
- **`e2e-implementer`** — Creates/reruns Playwright E2E tests in `apps/e2e`.
- **`test-implementer`** — Implements unit tests following valid architecture and best practices.
- **`codegraph`** — Queries and maintains the CodeGraph code-intelligence index (`explore`, `node`, `impact`, `affected`); the default for codebase questions.
- **`version-bumper`** — Bumps the version of any `apps/*` module following semver.
- **`dependabot-agent`** — Processes open GitHub Dependabot PRs.
- **`gh-actions-debug`** — Debugs GitHub Actions / Dependabot run failures with `gh`.
- **`scrapling-implementer`** — Scrapling library usage (fetching, parsing, spiders).
- **`crawlee-page-analyst`** — Uses Crawlee to analyze a source page after a site/DOM change and produce scrapper-change requirements before editing selectors.
- **`view-backend-logs`** — How to view backend logs using docker-compose.

## Required Tools

Agentic workflows require **Docker**, **CodeGraph** (the default code-intelligence tool, installed by `scripts/install.*`, see [README_INSTALL.md](README_INSTALL.md)) and the **GitHub CLI (`gh`, see [README_INSTALL.md](README_INSTALL.md))**. `gh` is used by `dependabot-agent` (processing Dependabot PRs) and `gh-actions-debug` (inspecting workflow/Dependabot run logs, which the web UI hides behind a write-access link). **Crawlee** (`uv tool install "crawlee[all]"`, installed automatically by `scripts/install.*`, see [README_INSTALL.md](README_INSTALL.md)) is used by `crawlee-page-analyst` to analyze source-page changes.

## CodeGraph (code intelligence)

CodeGraph is the default way to explore the repository. It indexes the checkout into `.codegraph/` (local, gitignored) and exposes a CLI plus MCP tools (`codegraph_explore`, `codegraph_node`) that `codegraph install --yes` wires into the detected agents. The daemon watches the repo and auto-syncs changed files.

Agents should query CodeGraph before grepping or reading source files: use `codegraph_explore` (or `codegraph explore "<question>"`) for an area, `codegraph_node` / `codegraph node <symbol>` for one symbol, and `callers`/`callees`/`impact`/`affected` for relationships. Read raw files only for the lines the graph or an earlier read already located.

`.codegraph/` is generated, machine-local output: never hand-edit or commit it, and never count it as documentation. The daemon normally keeps it fresh; if `codegraph status` looks stale, run `codegraph sync`, then `codegraph index` as a last resort. `scripts/uninstall.*` remove the index (`codegraph uninit`) and the agent wiring/CLI (`codegraph uninstall --yes`). Full command reference: `.claude/skills/codegraph/SKILL.md`.

## Crawlee (source-page change analysis)

When an `apps/scrapper` change is required because a source page changed (DOM redesign, new URL pattern, moved to client-side rendering), the `crawlee-page-analyst` skill is the mandatory first step: fetch the live page with Crawlee, diff the DOM against the selectors the scrapper uses, and produce selector-level requirements **before** editing any scrapper code. The analysis decides which fields broke, which crawler class fits (static vs JS-rendered), and whether the fix affects the Selenium path, the Scrapling path, or both. Crawlee is installed as a host tool (`uv tool install "crawlee[all]"`, run automatically by `scripts/install.sh` / `scripts/install.bat`); see [README_INSTALL.md](README_INSTALL.md) and the skill at `.claude/skills/crawlee-page-analyst/SKILL.md`.

## Documentation Policy (fix if wrong, high-level only)

Documentation must stay accurate and useful — it is not a changelog. The policy is defined once in `.claude/rules/documentation-update.md` (an always-on rule, loaded by opencode through `instructions` and by any harness that reads `.claude/rules/`); harnesses only nudge for impactful paths:

| Mechanism | Harness | What it does |
|-----------|---------|--------------|
| `.claude/rules/documentation-update.md` | all | Canonical policy: fix what is wrong, user-visible/setup changes, high-level scope |
| `.claude/hooks/docs-sync.py` | Claude Code (`PreToolUse` on `Edit`/`MultiEdit`/`Write`/`NotebookEdit`) | Reminds once per session when a compose/env/manifest/apps/scripts path is edited |
| `.opencode/plugins/docs-sync.js` | opencode | Same reminder, printed once on the next bash call |

In practice: fix docs the change made factually wrong; update root `README.md` or `apps/<module>/README.md` only for user-visible features, API/UI contracts and setup/run steps; update this file plus the affected rule for hooks, guards, skills and workflows; skip refactors, tests and internals (use CodeGraph to explore the code). Keep the user-facing READMEs high-level and link here for mechanics.

`.codegraph/` is generated, machine-local output: refresh it with `codegraph sync`/`codegraph index`, never hand-edit it, and never count it as documentation.

## Database changes require user permission (enforced guardrail)

The `jobs` MySQL database is **live production data** — scraping, enrichment, applications, and manual curation write to it continuously. A data or schema mutation is therefore never the agent's own initiative: measure the current state with read-only SQL, state the exact statement and the expected row count, then wait for the user to say yes. The policy is defined once in `.claude/rules/db-mutation-permission.md` and is **enforced in the tool call itself**, so it does not depend on the agent remembering it:

| Mechanism | Harness | What it does |
|-----------|---------|--------------|
| `.claude/rules/db-mutation-permission.md` | all | Canonical policy: what is blocked, what stays allowed, and how to ask |
| `.claude/hooks/db-mutation.py` | Claude Code (`PreToolUse` on `Bash`) | Exits 2 and denies the call, printing the reason and the remediation on stderr |
| `.opencode/plugins/db-mutation.js` | opencode | Throws from `tool.execute.before`, aborting the `bash` call with the same message |

Both are registered automatically: the hook in `.claude/settings.json` (`PreToolUse` → `Bash`), the plugin auto-discovered from `.opencode/plugins/db-mutation.js` in opencode (V2 default export). Both mirror each other and share the same detection logic, verified by an identical 31-case allow/block matrix.

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

## The test suite must run after code changes (enforced guardrail)

`apps/commonlib/commonlib/test/architecture_test.py` is the **only** place the repository's architecture rules are enforced: file length (200-line soft limit), backend layering, test-file naming, sibling-test correspondence, bare `print()`, and the `console=` logging contract. It lives in commonlib, so it executes **only when commonlib is one of the modules passed to the centralized test script** — a runner call that omits `commonlib` silently skips every architecture check.

The requirement is therefore enforced in the tool call, so it does not depend on the agent remembering it:

| Mechanism | Harness | What it does |
|-----------|---------|--------------|
| `.claude/rules/test-enforcement.md` | all | Canonical policy: which changes require the suite, and how it must be invoked |
| `.claude/hooks/test-enforce.py` | Claude Code (`PreToolUse` on `Edit`/`MultiEdit`/`Write`/`NotebookEdit` and on `Bash`) | Tracks the changed files, adds `commonlib` and the pending modules to a `scripts/test.sh` / `scripts/test.bat` invocation, and injects a reminder with the exact command to run |
| `.opencode/plugins/test-enforce.js` | opencode | Same behavior: injects the missing targets into a test-runner call and prints the reminder once on the next shell call |

Both are registered automatically: the hook in `.claude/settings.json`, the plugin in `.opencode/opencode.json`. They mirror each other, and both work the same way:

1. An edit to a file that requires the suite is recorded, together with the module it belongs to.
2. The next `scripts/test.sh` / `scripts/test.bat` invocation gets `commonlib` plus every recorded module added to its target list (`./scripts/test.sh web` → `./scripts/test.sh commonlib web`), so the architecture tests always execute.
3. If the agent runs any other shell command first, the reminder is prepended once, naming the exact command to run.

A runner invocation with **no** targets is left alone — the script already runs commonlib first, then every other module, then the e2e suite. Only real invocations are rewritten: a runner path that is a quoted string or an argument of another command (`echo "./scripts/test.sh web"`, `cat scripts/test.sh`) is left untouched, and every invocation of a compound command (`a && ./scripts/test.sh web && ./scripts/test.sh e2e`) is fixed.

Changes that require the suite: `apps/**/*.py`, `apps/web/src/**`, `apps/e2e/**`, the test runners themselves (`scripts/test.sh`, `scripts/test.bat`, any `test.*`), `.env*`, dependency manifests (`pyproject.toml`, `package.json`, `package-lock.json`, `uv.lock`, `poetry.lock`) and other `scripts/**` files. Changes that do **not** require it: documentation, CI workflows, coverage gates, install/sandbox helpers, agent rules and skills, and generated paths — state that reason in the summary when skipping.

## Dependabot PR workflow

The `dependabot-agent` skill processes open Dependabot PRs (they target `staging`; validated batches reach `master` only through the persistent `staging → master` promotion PR). The agent:

1. Runs the TDD pipeline for the affected module.
2. **Builds and runs** the affected Docker services in an isolated sandbox (`scripts/test-sandbox.*`, project `dependabot-test`) that renames containers, remaps ports, disables autodiscovery, clones the live `jobs` DB, and checks logs for errors.
3. Aborts the whole process on any build/start/log error.
4. Fixes failures and pushes so auto-merge can proceed.

Requires Docker and the GitHub CLI (`gh`, see [README_INSTALL.md](README_INSTALL.md)).

**Usage:** ask the agent to "process the open dependabot PRs" (optionally scoped to a module).

## Network Discovery

- **Scrapper MySQL**: `COMMONLIB_DB_HOST` supports single IPs, CIDR, ranges, and comma-separated combinations; the configured host is tried first, then the container chain (`mysql_db` → `host.docker.internal` → `127.0.0.1`), then an automatic LAN fallback. See [commonlib docs](../apps/commonlib/README.md#mysql-connection).
- **MongoDB**: `MONGO_URI` resolves the same way (`mongo_db` → `host.docker.internal` → `127.0.0.1`, then LAN on 27017; `auto` scans first). See [commonlib docs](../apps/commonlib/README.md#service-discovery-mysql--mongodb--ollama).
- **Web Backend API**: The web app resolves the backend at startup and watches it (`http://backend:8000` → `http://host.docker.internal:8000` → `http://localhost:8000` in Docker; reverse order on host). It waits for readiness (`BACKEND_WAIT_TIMEOUT_SECONDS`, default 120) and retries via watchdog (`BACKEND_CHECK_INTERVAL_SECONDS`, default 10, `BACKEND_MAX_RETRIES`, default 3). Pin with `BACKEND_URL`, allow LAN scan with `BACKEND_DISCOVERY=True`. See [web docs](../apps/web/README.md#backend-discovery).
- **Ollama**: Modules probe the configured URL (`AI_ENRICH_OLLAMA_BASE_URL`), then `host.docker.internal`, `localhost`, `ollama:11434`, then LAN scan on 11434 (disable with `COMMONLIB_OLLAMA_DISCOVERY=False`). Set `AI_ENRICH_OLLAMA_BASE_URL=auto` to scan directly. A one-token probe gates job submission (`COMMONLIB_OLLAMA_PROBE_TIMEOUT`, default 30s). Add subnets with `COMMONLIB_OLLAMA_DISCOVERY_SUBNETS` (e.g. `10.0.0.0/24`). See [commonlib docs](../apps/commonlib/README.md).
- **Watcher notifications**: After enrichment, `aiEnrich` POSTs enriched job IDs to the backend via `commonlib.watcher_notify` (auto-discovered like Ollama; pin with `AI_ENRICH_BACKEND_URL`). Best-effort (failures logged, enrichment continues). See [aiEnrich docs](../apps/aiEnrich/README.md#watcher-notification).
- **Dashboard health**: Backend probes Prometheus/Grafana on refresh (`GET /-/healthy`, `GET /api/health`). Configure `PROMETHEUS_URL` (default `http://host.docker.internal:9090`) and `GRAFANA_URL` (default `http://host.docker.internal:3000`).

## Related Documentation

- **Installation Guide**: [README_INSTALL.md](README_INSTALL.md)
- **Docker Development**: [DOCKER_DEV.md](DOCKER_DEV.md)
- **Contribution Guide**: [README_CONTRIBUTE.md](README_CONTRIBUTE.md)
- **GitHub Workflow**: [README_GITHUB.md](README_GITHUB.md)
