# AGENTS.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

AI Job Search is a monorepo for scraping, managing, and AI-enriching job offers from multiple platforms (LinkedIn, Infojobs, Glassdoor, Tecnoempleo, Indeed).

## Build and Development Commands

### Environment Setup
```bash
# Copy secrets template (never execute this, I have my credentials in .env.secrets)
cp scripts/.env.secrets.example .env.secrets

# Start services with Docker
docker-compose up -d
```

### Ollama: host vs container
The `ollama` service is opt-in (`--profile ollama`), so the stack works with Ollama installed on the host or containerized. No module hard-depends on the `ollama` container, so it never starts implicitly. The Ollama-backed modules (`aienrich`, `aienrichskill`) resolve the server at startup via the shared fallback chain in `commonlib/ollama_config.py`: configured URL, then `host.docker.internal`, `localhost`, then `ollama:11434`, then a LAN scan for port 11434 (`COMMONLIB_OLLAMA_DISCOVERY`, default on; `AI_ENRICH_OLLAMA_BASE_URL=auto` goes straight to the scan) — first reachable wins, reused for the whole batch. Each job is only sent after a one-token generation probe on that server (`COMMONLIB_OLLAMA_PROBE_TIMEOUT`, default 30s, reusing the job's own `num_ctx` so Ollama does not reload the model twice), so a wedged runner is skipped instead of blocking the whole job timeout; the verdict is cached per server for `COMMONLIB_OLLAMA_PROBE_CACHE_SECONDS` (default 300) and dropped again on a failed probe or a job timeout. The workers take the URL from `.env` (`docker-compose.yml` only defaults to the containerized `ollama:11434` when it is unset), and because a container's LAN scan only covers the Docker subnets, an Ollama on the physical LAN must be pinned with `AI_ENRICH_OLLAMA_BASE_URL` rather than discovered.
```bash
# Ollama on the host (nothing extra to start)
docker-compose --profile aienrich up -d aienrich
# Ollama containerized as well
docker-compose --profile ollama --profile aienrich up -d
```
Containers reach the host through `extra_hosts: host.docker.internal=host-gateway` (`backend`, `aienrich`, `aienrichskill`). Without it that name does not resolve and the workers crash-loop on `ollama.unreachable`.

### Sandboxed Docker Verification (dependabot-agent)
Brings a service up in an isolated `dependabot-test` project so the live `ai-job-search-*` stack and its data are never touched. Uses `docker-compose.test.override.yml` (renamed `-test` containers, remapped ports, data under `.docker-sandbox/`), and tears the sandbox down on exit.
```bash
# Windows
.\scripts\test-sandbox.bat <service> [--profile <name>] [--no-db-clone] [--keep]
# Linux/Mac
./scripts/test-sandbox.sh <service> [--profile <name>] [--no-db-clone] [--keep]

# Examples
.\scripts\test-sandbox.bat backend
.\scripts\test-sandbox.bat --profile aiEnrichSkill aienrichskill
```
- `backend` auto-clones the live MySQL `jobs` DB into the sandbox (via `scripts/mysql/backup.*`); skip with `--no-db-clone`.
- Mongo boots fresh/empty from `scripts/mongo/init.js`; ollama/prometheus/grafana are never duplicated.
- Profile-gated ai workers need their profile (`--profile aienrich|aiEnrichSkill`).
- Ollama-dependent services (`aienrich`, `aienrichskill`) are validated build-only + unit tests + ci-gate, not `up`.

### Python Apps (commonlib, scrapper)
```bash
# Install dependencies
poetry install
```

### Python Apps (backend, aiEnrich, aiEnrichSkill, aiCvMatcher)
```bash
# Install dependencies
uv sync
```

### Web Frontend (apps/web)
```bash
# Install
npm install

# Dev server
npm run dev

# Lint
npm run lint
```
Note: vitest 5 (apps/web) requires Node >= 22.12.0; prefer Node 24/26 (CI uses 24). If local Node is 22.12.0 and vitest workers fail with undici/zstd errors, use Node 24+ (e.g. `export PATH="$HOME/.nvm/versions/node/v26.8.2/bin:$PATH"`).

The dev server resolves the backend API at startup (`apps/web/src/common/backendResolver.ts`): it waits for a candidate to answer `/health` (`BACKEND_WAIT_TIMEOUT_SECONDS`, default 120) before serving, and a watchdog (`backendWatchdog.ts`) re-resolves the backend after `BACKEND_MAX_RETRIES` consecutive failures, retargeting the live Vite proxy. In Docker the candidates are `backend:8000` → `host.docker.internal:8000` → `localhost:8000`; the web service maps `host.docker.internal=host-gateway` through `extra_hosts`. The wait and the watchdog are skipped under vitest, so the test suite never waits for a running backend.

### E2E Tests (apps/e2e)
```bash
# Run Playwright tests
npm test

# Interactive UI mode
npm run test:ui

# Generate test code
npm run codegen
```

### Testing
Always use the centralized test script to run tests. Never run `poetry run pytest`, `uv run pytest`, or `npm test` directly. Always include `commonlib` as it contains architecture tests and is a shared library; also include any other modified `apps/*` modules.
```bash
# Run all tests (Linux/Mac)
./scripts/test.sh

# Run all tests (Windows)
.\scripts\test.bat

# Run commonlib + specific modified apps (Linux/Mac)
./scripts/test.sh commonlib scrapper web e2e

# Run commonlib + specific modified apps (Windows)
.\scripts\test.bat commonlib scrapper web e2e

# With coverage (also runs the web+scrapper coverage gates)
./scripts/test.sh --coverage
```

Coverage floors are 90% on **statements and lines** (functions and branches are reported only). The frontend gate runs on the union of web unit and e2e coverage; the scrapper gate on production statements only. See [READMEs/README_DEVELOPMENT.md](READMEs/README_DEVELOPMENT.md#coverage-gates).

Run the suites when the change touches test code, production code, or the test runner scripts (`scripts/test.sh`, `scripts/test.bat`). Skip them when the change is limited to documentation or non-test scripts/config (CI workflows, coverage gates, install/sandbox helpers, agent rules and skills) - those are not exercised by the unit or e2e suites, so state in the summary that the suites were skipped for that reason.

This requirement is enforced in the tool call, not left to memory: `architecture_test.py` (file length, layering, test naming, sibling tests, bare `print()`, the `console=` contract) lives in commonlib, so a runner call that omits `commonlib` silently skips it.

| Mechanism | Harness | What it does |
|-----------|---------|--------------|
| `.claude/rules/test-enforcement.md` | all | Canonical policy: which changes require the suite and how it must be invoked |
| `.claude/hooks/test-enforce.py` | Claude Code (`PreToolUse` on `Edit`/`MultiEdit`/`Write`/`NotebookEdit` and on `Bash`) | Adds `commonlib` and the changed modules to a `scripts/test.sh` / `scripts/test.bat` invocation, and injects a reminder with the exact command to run |
| `.opencode/plugins/test-enforce.js` | opencode | Same behavior: injects the missing targets into a test-runner call and prints the reminder once on the next shell call |

Changes that require the suite: `apps/**/*.py`, `apps/web/src/**`, `apps/e2e/**`, the test runners themselves, `.env*`, dependency manifests (`pyproject.toml`, `package.json`, lock files) and other `scripts/**` files. Documentation, CI workflows, coverage gates, install/sandbox helpers and agent rules/skills do not.

### Static Analysis
Static analysis is a blocking CI gate (`static-analysis` job). Run it locally with the same entry point CI uses:
```bash
# Whole repo: ruff + web eslint/tsc + e2e eslint
./scripts/lint.sh          # or .\scripts\lint.bat

# Per target
./scripts/lint.sh python   # ruff over apps/ and scripts/ (root ruff.toml)
./scripts/lint.sh web      # eslint + tsc -b over apps/web
./scripts/lint.sh e2e      # eslint over apps/e2e
```
Ruff is installed once for the whole repo (`uv tool install ruff`); no app needs it in its own environment. Rules in force: `E9` (syntax errors), `F401` (unused imports), `F841` (unused variables), `F811` (dead redefinitions), `ARG` (unused arguments) and the whole flake8-bugbear set (`B`, 44 rules). The bugbear rules that shaped the codebase the most: `B007` (unused loop variables), `B008` (call in an argument default), `B011` (`assert False`), `B017` (blind `pytest.raises(Exception)`), `B018` (useless expressions), `B027` (empty abstract methods), `B028` (`warnings.warn` without `stacklevel`), `B034` (positional `re.sub` arguments), `B904` (`raise ... from`), `B905` (`zip(strict=)`). FastAPI `Depends`/`Query` defaults are allowed for `B008`.

Prefix an intentionally unused parameter with `_` (`_properties`) instead of deleting it. Use `# noqa: ARG00x - <reason>` only when the signature is fixed by a contract (structlog processors, markdownify overrides, navigator/executor interfaces). `ARG` is **not** enforced on pytest modules, because pytest resolves a fixture by the name of the test parameter, so an unused one cannot be renamed without breaking fixture resolution.

The same rules run before the commit on the changed files only, via [pre-commit](https://pre-commit.com/) (`.pre-commit-config.yaml`: `ruff-check`, `eslint-web`, `eslint-e2e`). Install it with `pre-commit install`; the two ESLint hooks need `npm install` to have run in `apps/web` and `apps/e2e`. VS Code is wired to the same tools in `.vscode/settings.json`.

Details: [READMEs/README_DEVELOPMENT.md#static-analysis](READMEs/README_DEVELOPMENT.md#static-analysis).

### Running Individual Apps
```bash
# Backend API
uv run uvicorn main:app --reload --port 8000  # from apps/backend

# Web UI
npm run dev  # from apps/web, runs on localhost:5173

# Scrapper (loop mode)
.\apps\scrapper\run.bat  # or run.sh

# Scrapper (single platform)
.\apps\scrapper\run.bat linkedin

# AI Enrichment
.\apps\aiEnrich\run.bat  # or run.sh
.\apps\aiEnrichSkill\run.bat  # or run.sh
.\apps\aiCvMatcher\run.bat  # or run.sh
```

## Architecture

### Module Dependency Graph
```
commonlib ← backend
commonlib ← scrapper  
commonlib ← aiEnrich
commonlib ← aiEnrichSkill
commonlib ← aiCvMatcher
backend ← web (via REST API)
```

### Key Components

**commonlib** (`apps/commonlib/commonlib/`)
- Shared library used by all Python apps
- `mysqlUtil.py`, `sqlUtil.py`: Database access layer
- `aiEnrichRepository.py`: AI enrichment data persistence
- `skill_enricher_service.py`: Skill extraction logic
- Installed as local dependency: `commonlib = {path = "../commonlib", develop = true}`

**backend** (`apps/backend/`)
- FastAPI REST API serving the web frontend
- Entry point: `main.py`
- API docs at `/docs` (Swagger) and `/redoc`
- **Repositories** (`repositories/`):
  - `jobs_repository.py`: Facade for backward compatibility
  - `jobReadRepository.py`: Read operations (list, count, fetch)
  - `jobWriteRepository.py`: Write operations (create, update)
  - `jobDeleteRepository.py`: Delete operations with transaction support
  - `jobQueryRepository.py`: Query operations for applied jobs
  - `statistics_repository.py`: Statistics queries
  - `snapshots_repository.py`: Job snapshots for historical data
  - `combinedStatsRepository.py`: Combined stats (active + archived)

**web** (`apps/web/src/`)
- React 19 + TypeScript + Vite frontend
- State: TanStack Query (React Query)
- Routing: React Router
- Structure: `components/`, `pages/`, `hooks/`, `services/`, `types/`

**scrapper** (`apps/scrapper/scrapper/`)
- `navigator/`: Selenium browser automation per site (e.g., `linkedinNavigator.py`)
- `services/`: Business logic per site (e.g., `LinkedinService.py`)
- Coordinator scripts: `linkedin.py`, `infojobs.py`, etc.
- Supports `SCRAPPER_USE_UNDETECTED_CHROMEDRIVER=true` for bot detection bypass

**aiEnrichSkill** (`apps/aiEnrichSkill/`)
- Skill enrichment module supporting Ollama and HuggingFace backends
- Extracted from `aiEnrich` (Ollama)
- See `apps/aiEnrichSkill/README.md` for configuration

**aiCvMatcher** (`apps/aiCvMatcher/`)
- Local fast CV matching service
- Uses local `SentenceTransformers` from Hugging Face
- Operates on the pending CV match queue in the database


**e2e** (`apps/e2e/`)
- Playwright E2E tests for the web application

### Database
- MySQL 9 (Docker service `mysql_db`)
- Default credentials: `root/rootPass`, database: `jobs`
- Init scripts: `scripts/mysql/`

## Configuration

Environment variables are split across two files:
- `.env` (config): non-sensitive settings (cadencies, flags, URLs, model config)
- `.env.secrets` (credentials, copied from `scripts/.env.secrets.example`): emails, passwords, API keys
- `SCRAPPER_*_RUN_CADENCY`: Scraping frequency (e.g., `2h`, `40m`)
- `SCRAPPER_*_RUN_CADENCY_7-19=40m`: Time-based cadency override for specific hours
- `SCRAPPER_JOBS_SEARCH`: Comma-separated job search terms
- `AI_CVMATCHER_ENABLED=True`: Enable CV matching (uses the CV in `apps/aiCvMatcher/cv/cv.txt`)
- `SCRAPPER_USE_UNDETECTED_CHROMEDRIVER=True`: Bypass bot detection

## Code Style

- **Max line length**: 200 characters
- **Method signatures**: Keep parameters on the same line when possible, avoid line-per-parameter
- **Closing braces/parens**: Keep on the same line as last content, not on their own line
- **Method bodies**: Avoid extra spaces inside parentheses, e.g., `func(arg)` not `func( arg )`. Avoid empty lines inside method bodies.
- **Logging**: Structured events via `commonlib.observability` (see [Structured Logging](READMEs/README_DEVELOPMENT.md#structured-logging)). Bare `print()` is only allowed for presentational output listed in `PRINT_ALLOWLIST` in `apps/commonlib/commonlib/test/architecture/architecture_logging.py` — a commonlib architecture test enforces this.

## Documentation Sync (mandatory, automatic)

Documentation is part of the implementation, never a follow-up task. After **every** plan implementation, feature, fix, refactor, config change, or dependency bump, update the affected docs in the same session, before reporting the work as done. Never wait for the user to ask for it.

The rule is defined once in `.claude/rules/documentation-update.md` (always-on, auto-loaded via `instructions` in `.opencode/opencode.json`) and reinforced by `.claude/hooks/docs-sync.py` (Claude Code) and `.opencode/plugins/docs-sync.js` (opencode). Change → docs map, in short:

| Change | Docs to update |
|--------|-----------------|
| Behavior/feature/bug fix in `apps/<module>/` | `apps/<module>/README.md` |
| New/renamed/removed module in `apps/` | root `README.md`, `AGENTS.md`, `.claude/CLAUDE.md`, `READMEs/AGENTIC_SDLC.md` |
| Env var added/renamed/removed | root `README.md` (Settings), affected `apps/<module>/README.md` |
| Docker service, profile, port, volume | `READMEs/DOCKER_DEV.md`, root `README.md` (Docker Compose Profiles), `AGENTS.md` |
| Build/test/install/run command | `AGENTS.md`, `.claude/CLAUDE.md`, `READMEs/README_DEVELOPMENT.md` |
| New host tool (Docker, `gh`, Ollama model) | `READMEs/README_INSTALL.md` |
| Backend endpoint / DB schema | `apps/backend/README.md` |
| User-visible UI flow | root `README.md` (Features, Screenshots) |
| CI / Dependabot behavior | `READMEs/README_GITHUB.md` |
| Agent skill/rule/hook/plugin | `READMEs/AGENTIC_SDLC.md`, `AGENTS.md` + `.claude/CLAUDE.md` (Skills) |
| Plan implementation | the plan file (`Status:` + outcome), `READMZs/TODO.md` |

Before reporting done: open every listed doc, fix only what the change made inaccurate, and list the updated docs in the final summary (or state that none were needed). `.codegraph/` is generated, machine-local output — rebuild it with `codegraph index`/`sync`, never hand-edit it, and never count it as documentation.

## Database Safety (ask before any write)

The `jobs` MySQL database is live production data. **Never execute a data or schema mutation on your own initiative.** Measure the current state with read-only SQL, state the exact statement and the expected row count, then wait for the user's explicit "yes". This covers `INSERT`/`UPDATE`/`DELETE`/`DROP`/`TRUNCATE`/`ALTER`/`CREATE`/`GRANT`, piping a `.sql` file into a client, mongo/redis writes, and volume-destroying commands such as `docker compose down -v`. Read-only access (`SELECT`, `SHOW`, `EXPLAIN`, logs, `.env`, `docker compose restart`) is always fine.

Enforced by `.claude/rules/db-mutation-permission.md` + `.claude/hooks/db-mutation.py` (Claude Code) and `.opencode/plugins/db-mutation.js` (opencode), which **block the tool call**. After the user approves a specific statement, re-run it with the `AI_DB_WRITE_APPROVED` token in the command. Details: [READMEs/AGENTIC_SDLC.md](READMEs/AGENTIC_SDLC.md#database-changes-require-user-permission-enforced-guardrail).

## Skills

Agent skills are located in `.claude/skills/`:
- `skill-builder`: Create new agent skills
- `e2e-implementer`: Create Playwright E2E tests
- `test-implementer`: Implement unit tests
- `codegraph`: Query the CodeGraph code-intelligence index (explore/node/impact/affected); the default for codebase questions
- `version-bumper`: Bump the version of any apps/* module following semver
- `dependabot-agent`: Process open GitHub Dependabot PRs
- `gh-actions-debug`: Debug GitHub Actions / Dependabot run failures with the gh CLI
- `scrapling-implementer`: Scrapling library usage (fetching, parsing, spiders)
- `crawlee-page-analyst`: Analyze a source page that changed (DOM/URL redesign) with Crawlee before changing `apps/scrapper`, producing selector-level requirements
- `view-backend-logs`: How to view backend logs using docker-compose

## CodeGraph (code intelligence)

CodeGraph is the project's default code-intelligence tool. Its index lives in the local, gitignored `.codegraph/` directory; the background daemon auto-syncs changed files, and `scripts/install.*` install the CLI, wire its MCP server into the detected agents, and build the initial index.

Rules:
- For codebase questions, use CodeGraph before your first grep, search or source-file read, and put this rule in every subagent prompt that explores code. Use the `codegraph_explore` MCP tool when available, otherwise `codegraph explore "<question>"`. Use `codegraph_node` / `codegraph node <symbol>` for one symbol, and `callers`/`callees`/`impact`/`affected` for relationships. See `.claude/skills/codegraph/SKILL.md`.
- Read raw files only for lines CodeGraph or an earlier read already located.
- `.codegraph/` is generated and local: never hand-edit it, never commit it, and never count it as documentation.
- After substantial changes, check `codegraph status`; the daemon normally syncs automatically, otherwise run `codegraph sync`.
