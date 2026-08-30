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
| **aiEnrichNew** | `apps/aiEnrichNew/` | Python, Hugging Face | uv |
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
cd apps/backend  # or apps/aiEnrichNew
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

# Backend (uv)
cd apps/backend
uv sync            # Install deps
uv run uvicorn main:app --reload --port 8000

# Legacy apps (Poetry)
cd apps/scrapper
poetry install
poetry run pytest
```

## Code Style Guidelines

### Python (Commonlib, Backend, Scrapper)
- **Imports**: Group in order: stdlib, third-party, local imports
- **Types**: Use Python 3.10+ type hints consistently
- **Naming**: snake_case for variables/functions, PascalCase for classes
- **Error Handling**: Use specific exceptions, avoid bare except clauses
- **Dependencies**: uv for new projects, Poetry for legacy (commonlib, scrapper)
- **Testing**: pytest with `test_` prefix, use fixtures for setup/teardown. Use `@pytest.mark.parametrize` with descriptive `id=` for repetitive test cases.

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
2. **Tests pass**: Ensure all related tests pass after changes
3. **Lint/TypeScript clean**: Run linting and type checking commands

```bash
# Quick check for architecture violations (always run before finishing)
cd apps/web && npx vitest run src/test/architecture.test.ts
cd apps/commonlib && poetry run pytest test/architecture_test.py
```

## Testing Requirements

- **Coverage**: Minimum 85% for all apps, generate badges with `--coverage`
- **Test Order**: commonlib tests run first, then other apps, then E2E
- **Windows Compatibility**: Use appropriate conditional blocks for OS-specific code

## Environment Setup

```bash
# Full stack development
docker-compose up -d  # MySQL, Backend, Web, aiEnrichNew

# Install all dependencies
./scripts/install.sh   # Linux/Mac
.\scripts\install.bat  # Windows
```

## Skills

Agent skills are located in `.claude/skills/`:
- `skill-builder`: Create new agent skills
- `e2e-implementer`: Create Playwright E2E tests
- `test-implementer`: Implement unit tests
- `scrapling-implementer`: Scrapling scraping library usage (fetching, parsing, spiders)
- `view-backend-logs`: How to view backend logs using docker-compose
- `version-bumper`: Bump the version of any apps/* module following semver
- `dependabot-agent`: Process open GitHub Dependabot PRs
- `graphify`: Query the repo knowledge graph (query/path/explain)
- `graphify-dev`: Change/improve graphify functionality (visualization, pipeline scripts). MANDATORY before editing anything graphify-related — never modify the uv-installed graphify package.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Always run graphify through the wrapper scripts — `scripts\graphify\graphify.bat` (Windows) or `scripts/graphify/graphify.sh` (Linux/Mac) — never the raw `graphify` binary. The wrapper owns the full pipeline (no args = rebuild, `--clean`, `--module <name>`) and delegates `query`/`path`/`explain` to the CLI; mutating subcommands (`update`, `cluster-only`, `add`, `export`, `extract`, `merge-graphs`, URLs) are delegated and then re-run the repo HTML generator.

`graphify-out/graph.html` is repo-owned: it is generated ONLY by `python scripts/graphify/graphify-html-grouped.py` (module-grouped visualization). Never regenerate it with upstream CLI commands (`graphify export html`, bare `graphify update .`, `graphify cluster-only`, path builds) — they overwrite it with the default/aggregated output.

Rules:
- For codebase questions, first run the wrapper `query` subcommand (e.g. `scripts\graphify\graphify.bat query "<question>"`) when graphify-out/graph.json exists. Use `path` for relationships and `explain` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run the wrapper `update` subcommand (e.g. `scripts\graphify\graphify.bat update .`) to keep the graph current (AST-only, no API cost).
