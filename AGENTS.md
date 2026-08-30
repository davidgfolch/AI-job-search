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

### Sandboxed Docker Verification (dependabot-agent)
Brings a service up in an isolated `dependabot-test` project so the live `ai-job-search-*` stack and its data are never touched. Uses `docker-compose.test.override.yml` (renamed `-test` containers, remapped ports, data under `.docker-sandbox/`), and tears the sandbox down on exit.
```bash
# Windows
.\scripts\test-sandbox.bat <service> [--profile <name>] [--no-db-clone] [--keep]
# Linux/Mac
./scripts/test-sandbox.sh <service> [--profile <name>] [--no-db-clone] [--keep]

# Examples
.\scripts\test-sandbox.bat backend
.\scripts\test-sandbox.bat --profile aiEnrichNew aienrichnew
```
- `backend` auto-clones the live MySQL `jobs` DB into the sandbox (via `scripts/mysql/backup.*`); skip with `--no-db-clone`.
- Mongo boots fresh/empty from `scripts/mongo/init.js`; ollama/prometheus/grafana are never duplicated.
- Profile-gated ai workers need their profile (`--profile aienrich|aiEnrichNew|aiEnrichSkill|aiEnrich3`).
- Ollama-dependent services (`aienrich`, `aienrichskill`, `scrapper`) are validated build-only + unit tests + ci-gate, not `up`.

### Python Apps (commonlib, scrapper)
```bash
# Install dependencies
poetry install

# Run tests
poetry run pytest

# Run tests with coverage
poetry run coverage run -m pytest && poetry run coverage report -m
```

### Python Apps (backend, aiEnrich, aiEnrich3, aiEnrichNew, aiEnrichSkill, aiCvMatcher)
```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Run tests with coverage
uv run coverage run -m pytest && uv run coverage report -m
```

### Web Frontend (apps/web)
```bash
# Install
npm install

# Dev server
npm run dev

# Test
npm test

# Lint
npm run lint
```

### E2E Tests (apps/e2e)
```bash
# Run Playwright tests
npm test

# Interactive UI mode
npm run test:ui

# Generate test code
npm run codegen
```

### Monorepo-wide Testing
```bash
# Run all tests (Linux/Mac)
./scripts/test.sh

# Run all tests (Windows)
.\scripts\test.bat

# Run specific apps
.\scripts\test.bat commonlib web e2e

# With coverage
.\scripts\test.bat --coverage
```

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
.\apps\aiEnrich3\run.bat  # or run.sh
.\apps\aiEnrichNew\run.bat  # or run.sh
.\apps\aiEnrichSkill\run.bat  # or run.sh
.\apps\aiCvMatcher\run.bat  # or run.sh
```

## Architecture

### Module Dependency Graph
```
commonlib ← backend
commonlib ← scrapper  
commonlib ← aiEnrich
commonlib ← aiEnrich3
commonlib ← aiEnrichNew
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

**aiEnrichNew** (`apps/aiEnrichNew/`)
- Local Hugging Face transformers for job data enrichment
- Model: `Qwen/Qwen2.5-1.5B-Instruct` (configurable in `dataExtractor.py`)
- Preferred over `aiEnrich` (Ollama)

**aiEnrichSkill** (`apps/aiEnrichSkill/`)
- Skill enrichment module supporting Ollama and HuggingFace backends
- Extracted from `aiEnrich` (Ollama) and `aiEnrichNew` (HuggingFace)
- See `apps/aiEnrichSkill/README.md` for configuration

**aiEnrich3** (`apps/aiEnrich3/`)
- CPU-optimized multilingual data extraction service
- Uses GLiNER, mDeBERTa, and Regex
- Fast alternative to `aiEnrich` when GPUs are not available

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
- `AI_CV_MATCH=True`: Enable CV matching (requires `apps/aiEnrich/cv/cv.txt`)
- `SCRAPPER_USE_UNDETECTED_CHROMEDRIVER=True`: Bypass bot detection

## Code Style

- **Max line length**: 200 characters
- **Method signatures**: Keep parameters on the same line when possible, avoid line-per-parameter
- **Closing braces/parens**: Keep on the same line as last content, not on their own line
- **Method bodies**: Avoid extra spaces inside parentheses, e.g., `func(arg)` not `func( arg )`. Avoid empty lines inside method bodies.

## Skills

Agent skills are located in `.claude/skills/`:
- `skill-builder`: Create new agent skills
- `e2e-implementer`: Create Playwright E2E tests
- `test-implementer`: Implement unit tests
- `graphify`: Query the repository knowledge graph (query/path/explain)
- `graphify-dev`: Change/improve graphify functionality (visualization, pipeline scripts). MANDATORY before editing anything graphify-related — never modify the uv-installed graphify package.
- `version-bumper`: Bump the version of any apps/* module following semver
- `dependabot-agent`: Process open GitHub Dependabot PRs
- `scrapling-implementer`: Scrapling library usage (fetching, parsing, spiders)
- `view-backend-logs`: How to view backend logs using docker-compose

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
