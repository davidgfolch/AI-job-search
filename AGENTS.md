# AGENTS.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

AI Job Search is a monorepo for scraping, managing, and AI-enriching job offers from multiple platforms (LinkedIn, Infojobs, Glassdoor, Tecnoempleo, Indeed).

## Build and Development Commands

### Environment Setup
```bash
# Copy environment config (never execute this, I have my credentials in .env)
cp scripts/.env.example .env

# Start services with Docker
docker-compose up -d
```

### Python Apps (commonlib, scrapper)
```bash
# Install dependencies
poetry install

# Run tests
poetry run pytest

# Run tests with coverage
poetry run coverage run -m pytest && poetry run coverage report -m
```

### Python Apps (backend, aiEnrich, aiEnrich3, aiEnrichNew, aiCvMatcher)
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
- Supports `USE_UNDETECTED_CHROMEDRIVER=true` for bot detection bypass

**aiEnrichNew** (`apps/aiEnrichNew/`)
- Local Hugging Face transformers for job data enrichment
- Model: `Qwen/Qwen2.5-1.5B-Instruct` (configurable in `dataExtractor.py`)
- Preferred over `aiEnrich` (CrewAI/Ollama)

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

Environment variables are defined in `.env` (copied from `scripts/.env.example`):
- `*_EMAIL`, `*_PWD`: Credentials per job platform
- `*_RUN_CADENCY`: Scraping frequency (e.g., `2h`, `40m`)
- `*_RUN_CADENCY_7-19=40m`: Time-based cadency override for specific hours
- `JOBS_SEARCH`: Comma-separated job search terms
- `AI_CV_MATCH=True`: Enable CV matching (requires `apps/aiEnrich/cv/cv.txt`)
- `USE_UNDETECTED_CHROMEDRIVER=True`: Bypass bot detection

## Code Style

- **Max line length**: 200 characters
- **Method signatures**: Keep parameters on the same line when possible, avoid line-per-parameter
- **Closing braces/parens**: Keep on the same line as last content, not on their own line
- **Method bodies**: Avoid extra spaces inside parentheses, e.g., `func(arg)` not `func( arg )`. Avoid empty lines inside method bodies.

## Skills

Agent skills are located in `.opencode/skills/`:
- `skill-builder`: Create new agent skills
- `e2e-implementer`: Create Playwright E2E tests
- `test-implementer`: Implement unit tests
