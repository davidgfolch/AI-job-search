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
| **AI Enrich**   | [`apps/aiEnrich`](apps/aiEnrich/README.md)           | AI agent to analyze job details (salary, skills). | Python, CrewAI, uv           |
| **AI Enrich New**| [`apps/aiEnrichNew`](apps/aiEnrichNew/README.md)    | Local AI enrichment using Transformers.           | Python, Transformers, uv     |

### Development with VS Code

To ensure VS Code automatically selects the correct interpreter for each project:

1. **Open the Workspace**: Open the `AI-job-search.code-workspace` file in VS Code (`File > Open Workspace from File...`).
2. **Interpreter Selection**: The workspace is configured to automatically pick up the `.venv` in each application folder (`apps/backend`, `apps/scrapper`, etc.).

## Getting Started

### Quick Start

- Copy `scripts/.env.example` to `.env`:
  - set your creadentials.
  - set your options (e.g., JOBS_SEARCH, CV_MATCH flag, etc.)
- Run dockerized applications, by default should run only:
  - MySQL
  - Backend API
  - Web UI
- Run apps/scrappers/run.(bat/sh) in terminal.
- Navigate to UI at [http://localhost:5173](http://localhost:5173)
- Run (optional) AiEnrichNew (using huddingface transformer no need to install ollama):
  - Run aiEnrichNew in separated terminals manually.
- ~~LEGACY: Run (optional) AiEnrich~~:
  - Install Ollama & llama3.2 model
  - Run aiEnrich in separated terminals manually.

NOTE: Ollama, scrapper & aiEnrich are not tested in docker yet, so you need to run them manually.

### Installation

Please see [README_INSTALL.md](READMEs/README_INSTALL.md) for detailed setup instructions.

### Run with Docker (Recommended for dev) 🐳

```bash
docker-compose up -d
docker-compose logs -f
```

See [DOCKER_DEV.md](DOCKER_DEV.md).

### Run Manually (Using Helper Scripts)

Each application includes convenience scripts (`run.sh` / `run.bat`) to start them easily.

#### Linux / macOS (`.sh`)

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

#### Windows (`.bat`)

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

## Testing

Run all tests across the monorepo:

- **Linux**: `./scripts/test.sh` (Optional: `--coverage`)
- **Windows**: `.\scripts\test.bat` (Optional: `--coverage`)

## Documentation

- **Installation**: [README_INSTALL.md](READMEs/README_INSTALL.md)
- **Contributing**: [README_CONTRIBUTE.md](READMEs/README_CONTRIBUTE.md)
- **Docker**: [DOCKER_DEV.md](DOCKER_DEV.md)
