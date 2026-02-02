# AI Job Search Monorepo  [![backend-build-lint-and-tests](https://github.com/davidgfolch/AI-job-search/actions/workflows/ci.yml/badge.svg)](https://github.com/davidgfolch/AI-job-search/actions/workflows/ci.yml)

![commonlib](apps/commonlib/coverage.svg)
![backend](apps/backend/coverage.svg)
![web](apps/web/coverage/badges.svg)
![aiEnrich](apps/aiEnrich/coverage.svg)
![aiEnrichNew](apps/aiEnrichNew/coverage.svg)
![scrapper](apps/scrapper/coverage.svg)

A comprehensive system to search, aggregate, and manage job offers from multiple platforms (LinkedIn, Infojobs, Glassdoor, etc.), enriched with AI.

## Project Structure

This is a monorepo containing several applications and packages:

| Component       | Path                                                 | Description                                       | Tech Stack                   |
| --------------- | ---------------------------------------------------- | ------------------------------------------------- | ---------------------------- |
| **Common Lib**  | [`apps/commonlib`](apps/commonlib/README.md)         | Shared Python utilities and database logic.       | Python, Poetry               |
| **Web UI**      | [`apps/web`](apps/web/README.md)                     | Modern React frontend for job management.         | React, TypeScript, Vite, npm |
| **Backend API** | [`apps/backend`](apps/backend/README.md)             | FastAPI backend serving the Web UI.               | Python, FastAPI, Poetry      |
| **Scrapper**    | [`apps/scrapper`](apps/scrapper/README.md)           | Selenium-based job scrapers.                      | Python, Selenium, Poetry     |
| **AI Enrich**   | [`apps/aiEnrich`](apps/aiEnrich/README.md)           | Local AI enrichment using Ollama (LEGACY)         | Python, CrewAI, uv           |
| **AI Enrich New**| [`apps/aiEnrichNew`](apps/aiEnrichNew/README.md)    | Local AI enrichment using Transformers.           | Python, Transformers, uv     |

## Features

- Scrapping jobs from multiple platforms
- UI to manage job offers (& skills)
- AI enrichment of job offers (& skills)

## Getting Started

### Quick Start

- Copy `scripts/.env.example` to `.env`:
  - set your creadentials.
  - set your options (e.g., JOBS_SEARCH, CV_MATCH flag, etc.)
- Run dockerized applications `docker-compose up -d`, by default should run only:
  - MySQL
  - Backend API
  - Web UI
  - AiEnrichNew
- Run `apps/scrappers/run.(bat/sh)` in terminal.
- Navigate to UI at [http://localhost:5173](http://localhost:5173)
- Run (optional)
- ~~LEGACY: Run (optional) AiEnrich~~:
  - ~~Install Ollama & llama3.2 model~~
  - ~~Run aiEnrich in separated terminals manually~~.

NOTE: Ollama, scrapper & aiEnrich (LEGACY) are not tested in docker yet, so you need to run them manually.

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
# (NEW and quicker)
./apps/aiEnrichNew/run.sh
# (OLD legacy and slower)
./apps/aiEnrich/run.sh

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
:: (NEW and quicker)
.\apps\aiEnrichNew\run.bat
:: (OLD legacy and slower)
.\apps\aiEnrich\run.bat

:: 4. New UI (Backend + Web)
.\apps\backend\run.bat
.\apps\web\run.bat
```



## Documentation

- **Installation**: [README_INSTALL.md](READMEs/README_INSTALL.md)
- **Development**: [README_DEVELOPMENT.md](READMEs/README_DEVELOPMENT.md)
- **Contributing**: [README_CONTRIBUTE.md](READMEs/README_CONTRIBUTE.md)
- **Docker**: [DOCKER_DEV.md](DOCKER_DEV.md)
