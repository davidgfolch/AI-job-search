# AI Job Search Monorepo  [![backend-build-lint-and-tests](https://github.com/davidgfolch/AI-job-search/actions/workflows/ci.yml/badge.svg)](https://github.com/davidgfolch/AI-job-search/actions/workflows/ci.yml)

![commonlib](apps/commonlib/coverage.svg)
![backend](apps/backend/coverage.svg)
![web](apps/web/coverage/badges.svg)
![aiEnrich](apps/aiEnrich/coverage.svg)
![aiEnrich3](apps/aiEnrich3/coverage.svg)
![aiEnrichNew](apps/aiEnrichNew/coverage.svg)
![scrapper](apps/scrapper/coverage.svg)
![aiCvMatcher](apps/aiCvMatcher/coverage.svg)

A comprehensive system to search, aggregate, and manage job offers from multiple platforms (LinkedIn, Infojobs, Glassdoor, etc.), enriched with AI.

## Project Structure

This is a monorepo containing several applications and packages:

| Component       | Path                                                 | Description                                       | Tech Stack                   |
| --------------- | ---------------------------------------------------- | ------------------------------------------------- | ---------------------------- |
| **Common Lib**  | [`apps/commonlib`](apps/commonlib/README.md)         | Shared Python utilities and database logic.       | Python, Poetry               |
| **Web UI**      | [`apps/web`](apps/web/README.md)                     | Modern React frontend for job management.         | React, TypeScript, Vite, npm |
| **Backend API** | [`apps/backend`](apps/backend/README.md)             | FastAPI backend serving the Web UI.               | Python, FastAPI, Poetry      |
| **Scrapper**    | [`apps/scrapper`](apps/scrapper/README.md)           | Selenium-based job scrapers.                      | Python, Selenium, Poetry     |
| **AI Enrich**   | [`apps/aiEnrich`](apps/aiEnrich/README.md)           | Local AI enrichment using Ollama                  | Python, CrewAI, uv           |
| **AI Enrich New**| [`apps/aiEnrichNew`](apps/aiEnrichNew/README.md)    | Local AI enrichment using transformers pipeline   | Python, HuggingFace, uv      |
| **AI Enrich 3** | [`apps/aiEnrich3`](apps/aiEnrich3/README.md)         | Local AI enrichment using CPU models (GLiNER & mDeBERTa). | Python, ML Models, uv        |
| **AI CV Matcher**| [`apps/aiCvMatcher`](apps/aiCvMatcher/README.md)    | Local fast CV matching.                           | Python, SentenceTransformers |

### Note on Root `pyproject.toml`
The root `pyproject.toml` is **not required** for deploying or running the applications, as each module (in `apps/`) has its own dependencies and configuration for Docker and CI/CD. However, it is **highly necessary for the local Developer Experience (DX)**. It configures the virtual environment used by the VS Code Workspace (`.venv`), providing global linting/formatting tools (like `black`, `ruff`, and `mypy`), and ensures the IDE can correctly resolve cross-module imports like `commonlib`.

## Features

- Scrapping jobs from multiple platforms
- UI to manage job offers (& skills)
- AI enrichment of job offers (salary, skills, work modality)
- AI enrichment of skills
- AI CV matching

## Getting Started

### Quick Start

- Copy `scripts/.env.example` to `.env`:
  - set your creadentials.
  - set your options (e.g., JOBS_SEARCH, CV_MATCH flag, etc.)
- Run dockerized applications `docker-compose up -d`, by default should run only:
  - MySQL
  - Backend API
  - Web UI
  - AiEnrich
- Run `apps/scrappers/run.(bat/sh)` in terminal.
- Navigate to UI at [http://localhost:5173](http://localhost:5173)
- Run (optional) alternative AI Enrichment tools:
  - Default runs `aiEnrich`. If you want to use the others:
  - Run `aiEnrich3` (local fast CPU models) with `docker-compose --profile aiEnrich3 up -d`.
  - Alternatively, `docker-compose --profile aiEnrichNew up -d` for the transformers-based engine.
- Run `aiCvMatcher` (local fast CV matching):
  - It runs by default via `docker-compose up -d` if enabled. Make sure `AI_CV_MATCH=True` is in your `.env`.

NOTE: scrapper is not tested in docker yet, so you need to run it manually.

### Installation

Please see [README_INSTALL.md](READMEs/README_INSTALL.md) for detailed setup instructions.

### Run with Docker 🐳

You can run for development or just to use it.

```bash
docker-compose up -d
docker-compose logs -f
```

See [DOCKER_DEV.md](READMEs/DOCKER_DEV.md).

## Run Manually (Using Helper Scripts)

Each application includes convenience scripts (`run.sh` / `run.bat`) to start them easily.

### Linux / macOS (`.sh`)

```bash
# 1. Database
./scripts/runMysql.sh

# 2. Scrappers
./apps/scrapper/run.sh

# 3. AI Enrichment
# (NEW CPU and quicker)
./apps/aiEnrich3/run.sh
# (NEW GPU/Transformers pipeline)
./apps/aiEnrichNew/run.sh
# (Using CrewAI and Ollama)
./apps/aiEnrich/run.sh
# (Local Fast CV Matcher)
./apps/aiCvMatcher/run.sh

# 4. New UI (Backend + Web)
./apps/backend/run.sh
./apps/web/run.sh
```

### Windows (`.bat`)

```cmd
:: 1. Database
docker compose up -d

:: 2. Scrappers
.\apps\scrapper\run.bat

:: 3. AI Enrichment
:: (NEW CPU and quicker)
.\apps\aiEnrich3\run.bat
:: (NEW GPU/Transformers pipeline)
.\apps\aiEnrichNew\run.bat
:: (Using CrewAI and Ollama)
.\apps\aiEnrich\run.bat
:: (Local Fast CV Matcher)
.\apps\aiCvMatcher\run.bat

:: 4. New UI (Backend + Web)
.\apps\backend\run.bat
.\apps\web\run.bat
```



## Documentation

- **Installation**: [README_INSTALL.md](READMEs/README_INSTALL.md)
- **Development**: [README_DEVELOPMENT.md](READMEs/README_DEVELOPMENT.md)
- **Contributing**: [README_CONTRIBUTE.md](READMEs/README_CONTRIBUTE.md)
- **Docker**: [DOCKER_DEV.md](DOCKER_DEV.md)
