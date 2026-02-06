# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a monorepo for an AI-powered job search application that scrapes job listings from multiple platforms (LinkedIn, Infojobs, Glassdoor, etc.), enriches them with AI, and provides a web interface for managing applications.

## Monorepo Structure

| Component | Path | Tech Stack |
|-----------|------|------------|
| **commonlib** | `apps/commonlib/` | Python, Poetry - Shared utilities |
| **scrapper** | `apps/scrapper/` | Python, Selenium - Job scrapers |
| **backend** | `apps/backend/` | Python, FastAPI, uv - REST API |
| **aiEnrichNew** | `apps/aiEnrichNew/` | Python, uv, Hugging Face - AI enrichment |
| **web** | `apps/web/` | React, TypeScript, Vite - Frontend |

## Build & Test Commands

### Web Frontend (`apps/web`)
```bash
cd apps/web
npm install        # Install dependencies
npm run dev        # Start Vite dev server (port 5173)
npm run build      # Build for production
npm run lint       # ESLint
npm test           # Vitest unit tests
```

### Backend (`apps/backend`)
```bash
cd apps/backend
uv sync            # Install dependencies
uv run uvicorn main:app --reload --port 8000  # Run dev server
uv run pytest      # Run tests
```

### Scrapper (`apps/scrapper`)
```bash
cd apps/scrapper
poetry install     # Install dependencies
poetry run pytest  # Run tests
./run.sh           # Execute scrapers (infinite loop)
```

### AI Enrichment (`apps/aiEnrichNew`)
```bash
cd apps/aiEnrichNew
uv sync            # Install dependencies
uv run aienrichnew # Run enrichment
```

### All Tests
```bash
./scripts/test.sh      # Linux/Mac
.\scripts\test.bat     # Windows
```

## Architecture

### Backend (FastAPI)
**Layered architecture:**
- `api/` - FastAPI route handlers (REST endpoints)
- `services/` - Business logic layer
- `repositories/` - Data access layer (jobs_query_builder.py for SQL filters)
- `models/` - Pydantic models

Uses SQLAlchemy-style repository pattern with `commonlib.mysqlUtil.MysqlUtil`.

### Frontend (React/TypeScript)
**State Management:**
- **TanStack Query** for server state caching
- **Custom hooks** for domain-specific state (see `apps/web/src/pages/viewer/hooks/`)

**Key Hooks:**
- `useViewer.ts` - Main viewer state orchestration
- `useJobsData.ts` - Job list fetching and pagination
- `useFilterWatcher.ts` - Polling-based job watcher (5min intervals)

**Component Structure:**
- `pages/viewer/` - Main job viewer with tabs (list/create/edit)
- `pages/skillsManager/` - Skills management page

## Important Conventions

1. **Python**: Use `uv` for new projects, `poetry` for legacy (`scrapper`, `commonlib`)
2. **React Hooks**: Custom hook pattern for state logic separation
3. **API Calls**: Centralized in `api/` directories, use axios with error handling
4. **Query Key Strategy**: TanStack Query uses `[entity, filters]` pattern
5. **Watcher Pattern**: Polling with 5-minute intervals, aggressive debouncing
6. **SQL Filters**: Raw SQL supported via `sql_filter` parameter
7. **Docker**: `docker-compose up -d` starts core services (MySQL, Backend, Web, aiEnrichNew)
8. **Testing**: `./scripts/test.sh` for Linux/Mac, `./scripts/test.bat` for Windows, or specific module `./scripts/test.sh <module_name>`. Always run `commonlib\test\architecture_test.py` and for apps/web run `src\test\architecture.test.ts`.
9. **Documentation in code**: Avoid comments or docstrings to explain code logic, this is a monorepo and the code should be self-explanatory.

## Key Features

- **Multi-platform scraping**: LinkedIn, Infojobs, Glassdoor, Tecnoempleo, Indeed
- **AI enrichment**: Local Hugging Face models for extracting tech stack, salary
- **Job management**: Mark as applied/interviewing/rejected/ignored
- **Filter configurations**: Save/load filter presets with browser notifications
- **Statistics**: Charts showing job sources by date/time/day of week
