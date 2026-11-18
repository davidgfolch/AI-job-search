# Agentic SDLC

This document centralizes how agentic coding assistants (opencode, Claude Code) work with this repository: where their configuration lives, the skills they expose, and the workflows they drive (CodeGraph exploration, Dependabot processing, and more).

## Agent Homes

Agentic configuration and rules are consolidated under `.claude/` as the canonical home.

| Directory | Purpose |
|-----------|---------|
| `.claude/skills/` | Canonical home for all agent skills |
| `.claude/rules/` | Shared rule files (`architecture-guidelines.md`, `branch-workflow.md`, `docker-build.md`, `documentation-update.md`, `db-mutation-permission.md`, `test-enforcement.md`); opencode loads them all via `instructions` in `.opencode/opencode.json` |
| `.claude/hooks/` | Claude Code `PreToolUse` hooks (`docker-build.py`, `docs-sync.py`, `db-mutation.py`, `test-enforce.py`) and their shared logic (`lib/`) |
| `.claude/CLAUDE.md` | Agent guidance for Claude Code (repo overview, build/test commands, code style) |
| `.claude/settings.json` | Project-shared Claude Code settings (hooks) |
| `.claude/settings.local.json` | Local Claude Code permissions (not committed) |
| `.opencode/` | opencode-specific config only: `plugins/docker-build.js`, `plugins/docs-sync.js`, `plugins/db-mutation.js`, `plugins/test-enforce.js`, the shared plugin logic in `lib/`, `opencode.json`, and `plans/`. opencode plugins must live here (`issue #8158`) |

> **Note:** `.agent/` is retired. Skills and rules that previously lived in `.agent/` and the now-consolidated `.opencode/skills/` all live under `.claude/skills/` / `.claude/rules/` today.

## Skills

All agent skills live in `.claude/skills/`. Core ones:

- **`skill-builder`** — Creates new agent skills. Ask the agent to "create a new skill named [skill-name]".
- **`docs-writer`** — Writes/updates documentation under three rules: short root `README.md`, one canonical source per fact (DRY, links instead of copies) and operations documented through the centralized `scripts/*` entry points.
- **`e2e-implementer`** — Creates/reruns Playwright E2E tests in `apps/e2e`.
- **`test-implementer`** — Implements unit tests following valid architecture and best practices.
- **`codegraph`** — Queries and maintains the CodeGraph code-intelligence index (`explore`, `node`, `impact`, `affected`); the default for codebase questions.
- **`version-bumper`** — Bumps the version of any `apps/*` module following semver.
- **`dependabot-agent`** — Processes open GitHub Dependabot PRs in a throwaway sibling clone (`../ai_job_search_*`).
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

`apps/commonlib/commonlib/test/architecture_test.py` is the **only** place the repository's architecture rules are enforced: file length (200-line soft limit), layered architecture across Python modules (services must reach the database through a repository), test-file naming, sibling-test correspondence, bare `print()`, and the `console=` logging contract. It lives in commonlib, so it executes **only when commonlib is one of the modules passed to the centralized test script** — a runner call that omits `commonlib` silently skips every architecture check.

The requirement is therefore enforced in the tool call, so it does not depend on the agent remembering it:

| Mechanism | Harness | What it does |
|-----------|---------|--------------|
| `.claude/rules/test-enforcement.md` | all | Canonical policy: which changes require the suite, and how it must be invoked |
| `.claude/hooks/test-enforce.py` | Claude Code (`PreToolUse` on `Edit`/`MultiEdit`/`Write`/`NotebookEdit` and on `Bash`) | Tracks the changed files, adds `commonlib` and the pending modules to a `scripts/test.sh` / `scripts/test.bat` invocation, and injects a reminder with the exact command to run |
| `.opencode/plugins/test-enforce.js` | opencode | Same behavior: injects the missing targets into a test-runner call and prints the reminder once on the next shell call |

Both are registered automatically: the hook in `.claude/settings.json`, the plugin in `.opencode/opencode.json`. They mirror each other, and both work the same way:

1. An edit to a file that requires the suite is recorded, together with the module it belongs to.
2. The next `scripts/test.sh` / `scripts/test.bat` invocation gets `commonlib` plus every recorded module added to its target list (`./scripts/test.sh web` → `./scripts/test.sh commonlib web e2e`), so the architecture tests always execute. Web changes also pull in `e2e`; user-visible web changes must come with an added or updated E2E spec (`e2e-implementer` skill).
3. If the agent runs any other shell command first, the reminder is prepended once, naming the exact command to run.

A runner invocation with **no** targets is left alone — the script already runs commonlib first, then every other module, then the e2e suite. Only real invocations are rewritten: a runner path that is a quoted string or an argument of another command (`echo "./scripts/test.sh web"`, `cat scripts/test.sh`) is left untouched, and every invocation of a compound command (`a && ./scripts/test.sh web && ./scripts/test.sh e2e`) is fixed.

Changes that require the suite: `apps/**/*.py`, `apps/web/src/**` (also runs `e2e`), `apps/e2e/**`, the test runners themselves (`scripts/test.sh`, `scripts/test.bat`, any `test.*`), `.env*`, dependency manifests (`pyproject.toml`, `package.json`, `package-lock.json`, `uv.lock`, `poetry.lock`) and other `scripts/**` files. Changes that do **not** require it: documentation, CI workflows, coverage gates, install/sandbox helpers, agent rules and skills, and generated paths — state that reason in the summary when skipping.

## Branch workflow (master vs staging)

`master` is the default branch for every non-Dependabot change; `staging` is reserved for the Dependabot gate. The rule is defined once in `.claude/rules/branch-workflow.md` (always-on, loaded by both harnesses):

- **Dependabot session** — starts by syncing `master` into `staging` and ends by promoting `staging` into `master` when the batch is green; both happen in a dedicated session clone, never in the main workspace.
- **Any other session** — starts and ends on `master`; never commit a feature/fix/docs change to `staging`.
- If non-Dependabot commits end up on `staging`, promote them to `master` and fast-forward `staging` back to `master`.

## Dependabot PR workflow

The `dependabot-agent` skill processes open Dependabot PRs (they target `staging`; validated batches reach `master` only through the persistent `staging → master` promotion PR), and it is the **only** session that works on `staging` — every other change is done on `master` (see [branch workflow](#branch-workflow-master-vs-staging)). It runs entirely in throwaway sibling clones — a `../ai_job_search-dependabot-session` clone for the `staging` sync and the promotion, and one `../ai_job_search-dependabot-<pr>` clone per PR — so the main workspace, its branches and its running stack are never touched; the PR clones are deleted after their merge and the session clone after the promotion. This is the same per-feature clone flow `../rag-systems` uses with `scripts/dev.*`, available here as `scripts/dev.sh` / `scripts/dev.bat` (`new dependabot-session`, `sync` for the `staging` refresh, `dep <pr>` to create a PR clone, `cleanup dependabot-<pr>` / `cleanup dependabot-session` to delete them). The agent:

1. Syncs `master` into `staging` inside the session clone before anything else, so every PR is built on a current base; the main workspace is never checked out, pulled or pushed.
2. Runs the TDD pipeline for the affected module (installing it first, as `ci.yml` does).
3. **Builds and runs** the affected Docker services in an isolated sandbox (`scripts/test-sandbox.*`, project `dependabot-test`) that renames containers, remaps ports, disables autodiscovery, clones the live `jobs` DB, and checks logs for errors.
4. Aborts the whole process on any build/start/log error.
5. Fixes failures and pushes, then confirms the merge (grouped minor/patch PRs squash-merge automatically once `ci-gate` is green via `dependabot-auto-merge.yml`; everything else is merged explicitly).
6. When the batch is green, promotes `staging` into `master` through the promotion PR from the session clone, syncs both branches to the same commit, and deletes the session clone.

Requires Docker and the GitHub CLI (`gh`, see [README_INSTALL.md](README_INSTALL.md)).

**Usage:** ask the agent to "process the open dependabot PRs" (optionally scoped to a module).

## Network Discovery

Fallback chains, `.env` pins and LAN-scan knobs are documented once in [Distributed Execution & LAN Service Auto-Discovery](DISTRIBUTED_EXECUTION.md). Entry points per concern:

- **MySQL**: `COMMONLIB_DB_HOST` — [commonlib docs](../apps/commonlib/README.md#mysql-connection).
- **MongoDB**: `MONGO_URI` — [commonlib docs](../apps/commonlib/README.md#service-discovery-mysql--mongodb--ollama).
- **Web Backend API**: `BACKEND_URL` / `BACKEND_DISCOVERY`, readiness wait and watchdog — [web docs](../apps/web/README.md#backend-discovery).
- **Ollama**: `AI_ENRICH_OLLAMA_BASE_URL`, `COMMONLIB_OLLAMA_*` knobs — [commonlib docs](../apps/commonlib/README.md).
- **Watcher notifications**: `AI_ENRICH_BACKEND_URL`, best-effort delivery — [aiEnrich docs](../apps/aiEnrich/README.md#watcher-notification).
- **Dashboard health**: `PROMETHEUS_URL` / `GRAFANA_URL` — [DOCKER_DEV.md](DOCKER_DEV.md).

## Related Documentation

- **Installation Guide**: [README_INSTALL.md](README_INSTALL.md)
- **Docker Development**: [DOCKER_DEV.md](DOCKER_DEV.md)
- **Contribution Guide**: [README_CONTRIBUTE.md](README_CONTRIBUTE.md)
- **GitHub Workflow**: [README_GITHUB.md](README_GITHUB.md)
