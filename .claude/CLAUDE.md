# AGENTS.md

This file provides guidance to agentic coding assistants working with code in this repository.

## Project Overview

AI-powered job search monorepo with multi-platform scraping, AI enrichment, and web interface for managing job applications.

## Monorepo Structure

| Component | Path | Tech Stack | Package Manager |
|-----------|------|------------|----------------|
| **commonlib** | `apps/commonlib/` | Python utilities | Poetry |
| **scrapper** | `apps/scrapper/` | Python, Selenium | Poetry |
| **backend** | `apps/backend/` | Python, FastAPI | uv |
| **aiEnrich** | `apps/aiEnrich/` | Python, Ollama | uv |
| **aiEnrichSkill** | `apps/aiEnrichSkill/` | Python, Ollama & HuggingFace | uv |
| **aiCvMatcher** | `apps/aiCvMatcher/` | Python, SentenceTransformers | uv |
| **web** | `apps/web/` | React, TypeScript, Vite | npm |

## Build & Test Commands

### Single Test Execution
```bash
# Web frontend (Vitest)
cd apps/web
npm test -- path/to/specific.test.ts

# Backend/Python apps with uv
cd apps/backend  # or apps/aiEnrich
uv run pytest path/to/specific_test.py

# Legacy Python apps with Poetry  
cd apps/scrapper  # or apps/commonlib
poetry run pytest path/to/specific_test.py
```

### Full Suite & Coverage
```bash
# All tests with coverage
./scripts/test.sh --coverage

# Specific app tests (single or multiple)
./scripts/test.sh web
./scripts/test.sh backend
./scripts/test.sh commonlib web
./scripts/test.sh commonlib web e2e
./scripts/test.sh --coverage backend  # with coverage

# E2E tests only
./scripts/test.sh e2e
```

### Development & Linting
```bash
# Web frontend
cd apps/web
npm run dev        # Vite dev server (port 5173)
npm run build      # Production build
npm run lint       # ESLint
npm run typecheck  # tsc -b (type check only)

# Backend (uv)
cd apps/backend
uv sync            # Install deps
uv run uvicorn main:app --reload --port 8000

# Legacy apps (Poetry)
cd apps/scrapper
poetry install
poetry run pytest
```

### Static Analysis (blocking CI gate)
```bash
# Whole repo (ruff + web eslint/tsc + e2e eslint)
./scripts/lint.sh          # or .\scripts\lint.bat
./scripts/lint.sh python   # ruff over apps/ and scripts/ (root ruff.toml)
./scripts/lint.sh web      # eslint + tsc -b over apps/web
./scripts/lint.sh e2e      # eslint over apps/e2e
```
Ruff is installed once for the whole repo (`uv tool install ruff`); no app needs it in its
own environment. Rules in force: `E9`, `F401`, `F841`, `F811`, `ARG` and the whole flake8-bugbear set (`B`).
Prefix an intentionally unused parameter with `_` (`_properties`) instead of deleting it;
use `# noqa: ARG00x - <reason>` only when the signature is fixed by a contract (structlog
processors, markdownify overrides, navigator/executor interfaces). `ARG` is not enforced on
pytest modules, because pytest resolves fixtures by parameter name.
Details: [READMEs/README_DEVELOPMENT.md#static-analysis](READMEs/README_DEVELOPMENT.md#static-analysis).

## Code Style Guidelines

### Python (Commonlib, Backend, Scrapper)
- **Imports**: Group in order: stdlib, third-party, local imports
- **Types**: Use Python 3.10+ type hints consistently
- **Naming**: snake_case for variables/functions, PascalCase for classes
- **Error Handling**: Use specific exceptions, avoid bare except clauses
- **Dependencies**: uv for new projects, Poetry for legacy (commonlib, scrapper)
- **Testing**: pytest with `test_` prefix, use fixtures for setup/teardown. Use `@pytest.mark.parametrize` with descriptive `id=` for repetitive test cases.
- **Logging**: Structured events via `commonlib.observability` (root READMEs/README_DEVELOPMENT.md#structured-logging). Bare `print()` only for presentational output in the `PRINT_ALLOWLIST` (`apps/commonlib/commonlib/test/architecture/architecture_logging.py`) — enforced by a commonlib architecture test.

### TypeScript/React (Web Frontend)
- **Imports**: External libs first, then internal modules, avoid relative import hell
- **Types**: Strict TypeScript enabled, prefer explicit types over `any`
- **Components**: PascalCase for components, camelCase for functions/variables
- **Hooks**: Custom hooks pattern for state logic separation (see `apps/web/src/pages/viewer/hooks/`)
- **Testing**: Vitest with Testing Library, tests co-located with source files in `test/` subdirectories
- **React Act Warnings**: When testing hooks with `renderHook`, always wrap state updates in `act()`:
  ```typescript
  import { act } from '@testing-library/react';
  
  // ❌ Wrong - causes act(...) warning
  result.current.setTimeRange('Last week');
  await waitFor(() => expect(result.current.timeRange).toBe('Last week'));
  
  // ✅ Correct - wrapped in act()
  await act(async () => {
      result.current.setTimeRange('Last week');
  });
  await waitFor(() => expect(result.current.timeRange).toBe('Last week'));
  ```

### Architecture Patterns

#### Backend (FastAPI Layered)
```
api/          - Route handlers (FastAPI endpoints)
services/     - Business logic layer
repositories/ - Data access layer (use commonlib.sql.mysqlUtil.MysqlUtil)
models/       - Pydantic models
```
- API → Services → Repositories (no skipping layers)
- No direct database access from Services layer
- No circular dependencies between layers

#### Frontend (React/TypeScript)
- **State Management**: TanStack Query for server state, custom hooks for domain logic
- **Query Keys**: `[entity, filters]` pattern for TanStack Query
- **API Calls**: Centralized in `api/` directories using axios with error handling
- **Components**: Atomic design with pages/ as top-level organization

## Key Conventions

1. **Preserve Existing Code**: When editing files, only make changes necessary for the task at hand. Do NOT reformat, reword, or restyle code that isn't being intentionally modified. Preserve:
   - Original quote style (single vs double)
   - Original line breaks and spacing
   - Original variable/function naming
   - Original code structure unless refactoring is the explicit goal

2. **File Length**: Warn if files exceed 200 lines, fail at 300+ lines
2. **Test Location**: Tests must be in `test/` subdirectories parallel to source files
3. **Test Naming**: Test files should be `[ModuleName].test.ts` or `[module_name]_test.py`
4. **Polling**: Watcher patterns use 5-minute intervals with aggressive debouncing
5. **SQL**: Raw SQL supported via `sql_filter` parameter in backend APIs
6. **Documentation**: Avoid explanatory comments - code should be self-documenting

## Required Architecture Tests

Always run these after significant changes:
```bash
# Python architecture compliance & max files length including all apps/*
python apps/commonlib/commonlib/test/architecture_test.py

# Frontend architecture compliance  
npm test -- apps/web/src/test/architecture.test.ts
```

## Definition of Done

Before marking any task as complete, always verify:
1. **No architecture violations**: Run architecture tests to ensure no files exceed 200 lines
2. **Tests pass**: Ensure all related tests pass after changes — required when the change touches test code, production code, or `scripts/test.sh`/`scripts/test.bat`. Skip it when the change is only docs or non-test scripts/config (CI workflows, coverage gates, install/sandbox helpers, agent rules and skills) and say why in the summary.
3. **Lint/TypeScript clean**: Run linting and type checking commands
4. **Docs synced**: Apply the change → docs map in `.claude/rules/documentation-update.md` and list the updated docs in your summary (or state that none were needed)

```bash
# Quick check for architecture violations (always run before finishing)
cd apps/web && npx vitest run src/test/architecture.test.ts
cd apps/commonlib && poetry run pytest test/architecture_test.py
```

## Testing Requirements

- **Coverage**: 90% floor on statements and lines (functions/branches are reported only). The frontend is gated on the union of web unit + e2e coverage via `scripts/coverage/frontend-coverage-gate.mjs`; the scrapper via `scripts/coverage/scrapper_coverage_gate.py`. Generate badges with `--coverage`
- **Test Order**: commonlib tests run first, then other apps, then E2E
- **Windows Compatibility**: Use appropriate conditional blocks for OS-specific code

## Environment Setup

```bash
# Full stack development
docker-compose up -d  # MySQL, Backend, Web, aicvmatcher, aiformfiller

# Ollama is opt-in (`--profile ollama`): the Ollama-backed modules auto-detect a
# host-installed server via the fallback chain in commonlib/ollama_config.py, so
# add the profile only when you want Ollama itself containerized.
docker-compose --profile aienrich up -d aienrich
docker-compose --profile ollama --profile aienrich up -d

# Install all dependencies
./scripts/install.sh   # Linux/Mac
.\scripts\install.bat  # Windows

# Remove installed dependencies (interactive menu)
./scripts/uninstall.sh   # Linux/Mac
.\scripts\uninstall.bat  # Windows
```

## Documentation Sync (mandatory, automatic)

Documentation is updated in the same session as every plan implementation, feature, fix, refactor, config change, or dependency bump — never as a follow-up task, never only when the user asks. The rule lives in `.claude/rules/documentation-update.md` (change → docs map + definition-of-done checklist) and is reinforced by `.claude/hooks/docs-sync.py` and `.opencode/plugins/docs-sync.js`. Module behavior → `apps/<module>/README.md`; new module → root `README.md`, `AGENTS.md`, `.claude/CLAUDE.md`; env var → root `README.md`; compose change → `READMEs/DOCKER_DEV.md`; command change → `AGENTS.md`, `.claude/CLAUDE.md`, `READMEs/README_DEVELOPMENT.md`; new host tool → `READMEs/README_INSTALL.md`; API/DB → `apps/backend/README.md`; UI flow → root `README.md`; CI → `READMEs/README_GITHUB.md`; skill/rule/hook/plugin → `READMEs/AGENTIC_SDLC.md`; plan → the plan file + `READMZs/TODO.md`.

## Database Safety (ask before any write)

The `jobs` MySQL database is live production data: **never execute a data or schema mutation on your own initiative.** Measure first with read-only SQL (`SELECT`/`SHOW`/`EXPLAIN`), state the exact statement and the expected row count, then wait for the user's explicit "yes". Blocked without permission: `INSERT`/`UPDATE`/`DELETE`/`DROP`/`TRUNCATE`/`ALTER`/`CREATE`/`GRANT`, piping a `.sql` file into a client, mongo/redis writes, and volume-destroying commands (`docker compose down -v`, `docker volume rm`). The policy lives in `.claude/rules/db-mutation-permission.md` and is enforced in the tool call by `.claude/hooks/db-mutation.py` (Claude Code) and `.opencode/plugins/db-mutation.js` (opencode), which block it. After the user approves a specific statement, re-run it with the `AI_DB_WRITE_APPROVED` token in the command. Details: [READMEs/AGENTIC_SDLC.md](../READMEs/AGENTIC_SDLC.md#database-changes-require-user-permission-enforced-guardrail).

## Skills

Agent skills are located in `.claude/skills/`:
- `skill-builder`: Create new agent skills
- `e2e-implementer`: Create Playwright E2E tests
- `test-implementer`: Implement unit tests
- `codegraph`: Query the CodeGraph code-intelligence index (explore/node/impact/affected); the default for codebase questions
- `scrapling-implementer`: Scrapling scraping library usage (fetching, parsing, spiders)
- `crawlee-page-analyst`: Analyze a source page that changed (DOM/URL redesign) with Crawlee before changing `apps/scrapper`, producing selector-level requirements
- `view-backend-logs`: How to view backend logs using docker-compose
- `version-bumper`: Bump the version of any apps/* module following semver
- `dependabot-agent`: Process open GitHub Dependabot PRs
- `gh-actions-debug`: Debug GitHub Actions / Dependabot run failures with the gh CLI

## CodeGraph (code intelligence)

CodeGraph is the project's default code-intelligence tool. Its index lives in the local, gitignored `.codegraph/` directory; the background daemon auto-syncs changed files, and `scripts/install.*` install the CLI, wire its MCP server into the detected agents, and build the initial index.

Rules:
- For codebase questions, use CodeGraph before your first grep, search or source-file read, and put this rule in every subagent prompt that explores code. Use the `codegraph_explore` MCP tool when available, otherwise `codegraph explore "<question>"`. Use `codegraph_node` / `codegraph node <symbol>` for one symbol, and `callers`/`callees`/`impact`/`affected` for relationships. See `.claude/skills/codegraph/SKILL.md`.
- Read raw files only for lines CodeGraph or an earlier read already located.
- `.codegraph/` is generated and local: never hand-edit it, never commit it, and never count it as documentation.
- After substantial changes, check `codegraph status`; the daemon normally syncs automatically, otherwise run `codegraph sync`.
