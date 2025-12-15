# AI Job Search Monorepo

[![backend-build-lint-and-tests](https://github.com/davidgfolch/AI-job-search/actions/workflows/python-app.yml/badge.svg)](https://github.com/davidgfolch/AI-job-search/actions/workflows/python-app.yml)

| Module's coverage  |                                               | UI Module's coverage  |                                       |
| ------------------ | --------------------------------------------- | --------------------- | ------------------------------------- |
| packages/commonlib | ![commonlib](packages/commonlib/coverage.svg) | apps/viewer (old UI)  | ![viewer](apps/viewer/coverage.svg)   |
| apps/aiEnrich      | ![aiEnrich](apps/aiEnrich/coverage.svg)       | apps/web (new UI)     | ![web](apps/web/coverage/badges.svg)  |
| apps/scrapper      | ![scrapper](apps/scrapper/coverage.svg)       | apps/backend (new UI) | ![backend](apps/backend/coverage.svg) |

A comprehensive system to search, aggregate, and manage job offers from multiple platforms (LinkedIn, Infojobs, Glassdoor, etc.), enriched with AI.

## Project Structure

This is a monorepo containing several applications and packages:

| Component       | Path                                                 | Description                                       | Tech Stack                   |
| --------------- | ---------------------------------------------------- | ------------------------------------------------- | ---------------------------- |
| **Web UI**      | [`apps/web`](apps/web/README.md)                     | Modern React frontend for job management.         | React, TypeScript, Vite, npm |
| **Backend API** | [`apps/backend`](apps/backend/README.md)             | FastAPI backend serving the Web UI.               | Python, FastAPI, Poetry      |
| **Scrapper**    | [`apps/scrapper`](apps/scrapper/README.md)           | Selenium-based job scrapers.                      | Python, Selenium, Poetry     |
| **AI Enrich**   | [`apps/aiEnrich`](apps/aiEnrich/README.md)           | AI agent to analyze job details (salary, skills). | Python, CrewAI, uv           |
| **Common Lib**  | [`packages/commonlib`](packages/commonlib/README.md) | Shared Python utilities and database logic.       | Python, Poetry               |
| **Viewer**      | [`apps/viewer`](apps/viewer/README.md)               | Legacy Streamlit UI.                              | Python, Streamlit, Poetry    |

> **Note**: The **Viewer** application is the legacy interface. The **Web UI** + the **Backend** is the new, recommended implementation.

## Getting Started

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
./apps/aiEnrich/run.sh

# 4. New UI (Backend + Web)
./apps/backend/run.sh
./apps/web/run.sh

# 5. Legacy Viewer
./apps/viewer/run.sh
```

#### Windows (`.bat`)

```cmd
:: 1. Database
docker compose up -d

:: 2. Scrappers
.\apps\scrapper\run.bat

:: 3. AI Enrichment
.\apps\aiEnrich\run.bat

:: 4. New UI (Backend + Web)
.\apps\backend\run.bat
.\apps\web\run.bat

:: 5. Legacy Viewer
.\apps\viewer\run.bat
```

## Testing

Run all tests across the monorepo:

- **Linux**: `./scripts/test.sh` (Optional: `--coverage`)
- **Windows**: `.\scripts\test.bat` (Optional: `--coverage`)

## Documentation

- **Installation**: [README_INSTALL.md](READMEs/README_INSTALL.md)
- **Contributing**: [README_CONTRIBUTE.md](READMEs/README_CONTRIBUTE.md)
- **Docker**: [DOCKER_DEV.md](DOCKER_DEV.md)
