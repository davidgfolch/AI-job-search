# AI Job Search Monorepo  [![master CI](https://img.shields.io/github/actions/workflow/status/davidgfolch/AI-job-search/ci.yml?branch=master&label=master%20CI)](https://github.com/davidgfolch/AI-job-search/actions/workflows/ci.yml?branch=master)  [![staging CI](https://img.shields.io/github/actions/workflow/status/davidgfolch/AI-job-search/ci.yml?branch=staging&label=staging%20CI)](https://github.com/davidgfolch/AI-job-search/actions/workflows/ci.yml?branch=staging)

![commonlib](https://raw.githubusercontent.com/davidgfolch/AI-job-search/badges/apps/commonlib/coverage.svg)
![backend](https://raw.githubusercontent.com/davidgfolch/AI-job-search/badges/apps/backend/coverage.svg)
![web](https://raw.githubusercontent.com/davidgfolch/AI-job-search/badges/apps/web/coverage/badges.svg)
![aiEnrich](https://raw.githubusercontent.com/davidgfolch/AI-job-search/badges/apps/aiEnrich/coverage.svg)
![aiEnrichSkill](https://raw.githubusercontent.com/davidgfolch/AI-job-search/badges/apps/aiEnrichSkill/coverage.svg)
![scrapper](https://raw.githubusercontent.com/davidgfolch/AI-job-search/badges/apps/scrapper/coverage.svg)
![aiCvMatcher](https://raw.githubusercontent.com/davidgfolch/AI-job-search/badges/apps/aiCvMatcher/coverage.svg)
![aiFormFiller](https://raw.githubusercontent.com/davidgfolch/AI-job-search/badges/apps/aiFormFiller/coverage.svg)
![cron](https://raw.githubusercontent.com/davidgfolch/AI-job-search/badges/apps/cron/coverage.svg)
![e2e](https://raw.githubusercontent.com/davidgfolch/AI-job-search/badges/apps/e2e/coverage.svg)

> The `e2e` badge is the **frontend union** (web unit + e2e), the metric the 90% floor is
> enforced on; `web` is the unit run alone. See
> [Coverage Gates](READMEs/README_DEVELOPMENT.md#coverage-gates).

A comprehensive system to search, aggregate, and manage job offers from multiple platforms (LinkedIn, Infojobs, Glassdoor, etc.), enriched with AI job offer structured data extraction, skills/technologies description inference, etc.

## Project Structure

This is a monorepo containing several applications and packages:

| Component        | Path                                                 | Description                                               | Tech Stack                   |
| ---------------- | ---------------------------------------------------- | --------------------------------------------------------- | ---------------------------- |
| **Common Lib**   | [`apps/commonlib`](apps/commonlib/README.md)         | Shared Python utilities and database logic.               | Python, Poetry               |
| **Web UI**       | [`apps/web`](apps/web/README.md)                     | Modern React frontend for job management.                 | React, TypeScript, Vite, npm |
| **Backend API**  | [`apps/backend`](apps/backend/README.md)             | FastAPI backend serving the Web UI.                       | Python, FastAPI, Poetry      |
| **Cron**         | [`apps/cron`](apps/cron/README.md)                   | Background scheduler for periodic cron jobs.              | Python, uv, MongoDB          |
| **Scrapper**     | [`apps/scrapper`](apps/scrapper/README.md)           | Selenium-based job scrapers.                              | Python, Selenium, Poetry     |
| **AI Enrich**    | [`apps/aiEnrich`](apps/aiEnrich/README.md)           | AI enrichment using Ollama or OpenRouter                  | Python, Ollama/OpenRouter, uv |
| **AI Enrich Skill**| [`apps/aiEnrichSkill`](apps/aiEnrichSkill/README.md) | Local AI skill enrichment (Ollama & HuggingFace).        | Python, Transformers, uv     |
| **AI CV Matcher**| [`apps/aiCvMatcher`](apps/aiCvMatcher/README.md)     | Local fast CV matching.                                   | Python, SentenceTransformers |
| **AI Form Filler**| [`apps/aiFormFiller`](apps/aiFormFiller/README.md) | AI-powered form question answerer using CV + preferences. | Python, FastAPI, HuggingFace |

## Features

- Scrapping jobs from multiple platforms
- UI to manage job offers (& skills)
- AI enrichment of job offers (salary, skills, work modality)
- Deterministic salary scraping for the job boards that publish one (Indeed, Tecnoempleo), so the range is read from the offer instead of being left to the AI
- AI enrichment of skills
- AI enrichment of the company when a job board publishes the offer without one (stored as `unspecified` until inferred)
- AI CV matching
- AI Form Filler (browser extension + backend) to answer job application questions using your CV
- **Observability**: Structured logging + Prometheus metrics via `commonlib`; each app writes `data/logs/<app>.jsonl`, scraped by Prometheus (`:9090`) → Grafana (`:3000`, admin/admin); JSON API at `GET /api/enrichment/metrics` (see [Structured Logging](READMEs/README_DEVELOPMENT.md#structured-logging))
- **Settings UI** to manage `.env` / `.env.secrets` variables and scrapper state directly from the browser
- **Seamless API Routing**: Frontend automatically routes API requests seamlessly depending on environment (Docker bridge vs native localhost) and supports access from remote devices natively.

## CI / GitHub Automation

The CI pipeline, Dependabot version updates, and automatic merging of dependency PRs are documented in [GitHub Automation](READMEs/README_GITHUB.md). In short: CI only tests the modules affected by a change, Dependabot groups non-breaking updates per app, and green minor/patch Dependabot PRs auto-merge (majors stay manual; failing PRs never merge).

A separate `static-analysis` job is a **required check**: it lints every Python app with [Ruff](https://docs.astral.sh/ruff/), lints the frontend and the e2e suite with ESLint, and type-checks `apps/web` with `tsc`. Run the same checks locally with `./scripts/lint.sh` (see [Static Analysis](READMEs/README_DEVELOPMENT.md#static-analysis)).

## Distributed execution

You can set a specific MySQL host in `.env` via `COMMONLIB_DB_HOST` and run the scrapper on a separate machine connected to it (Linux recommended). Run only the web UI on a client machine:

```bash
docker-compose up -d --no-deps web
```

To run Ollama-backed workers on another machine in the same LAN (outside Docker):

```bash
./apps/aiEnrich/run.sh & ./apps/aiEnrichSkill/run.sh
```

### Network discovery

The MySQL host (`COMMONLIB_DB_HOST`), the web backend API, the Ollama server, the watcher notifications and the dashboard health probes are all auto-discovered on the LAN. Each concern, with its variables and fallback order, is documented once in [Network Discovery](READMEs/AGENTIC_SDLC.md#network-discovery) and in the module READMEs it points to.

## Screenshots

### UI Management

![UIScreenShot](READMEs/assets/UIScreenShot.png)

### AI daemons & fullstack app logs

![DockerCompose](READMEs/assets/DockerCompose.png)

### Scrapper

![Scrapper](READMEs/assets/Scrappers.png)

### Filters Configurations

![UIFiltersConfigurations](READMEs/assets/UIFiltersConfigurations.png)

### Skills Manager

![UISkillsManager](READMEs/assets/UISkillsManager.png)

### Skills Edit

![UISkillsEdit](READMEs/assets/UISkillsEdit.png)

### Stats

![UIStats](READMEs/assets/UIStats.png)

![UIDashboard](READMEs/assets/UIDashboard.png)

![Prometheus/Graphana](READMEs/assets/UIPrometheusGraphana.png)

### Stats Filter Configurations

![UIStatsFilterConfigurations](READMEs/assets/UIStatsFilterConfigurations.png)

### Settings — Environment Variables

![UISettings](READMEs/assets/UISettings.png)

### Settings — Scrapper State

![UISettingsScrapperState](READMEs/assets/UISettingsScrapperState.png)

## Getting Started

### Docker Compose Profiles

The `docker-compose.yml` groups services into profiles: the core services start by default, and the AI services (`aienrich`, `aiEnrichSkill`) plus the opt-in `ollama` server are selected with `--profile`. The profile table, the exact commands and the service URLs live in [DOCKER_DEV.md](READMEs/DOCKER_DEV.md).

The `web` service waits for the backend to answer before it serves, and reconnects to it when it moves, so it works with the backend containerized or running on the host (see [web backend discovery](apps/web/README.md#backend-discovery)).

#### Ollama: host vs container

The `ollama` service is **opt-in** (`--profile ollama`), so the stack works whether Ollama runs on your host or in Docker. The Ollama-backed modules (`aienrich`, `aienrichskill`) auto-detect the server at startup: they probe the configured URL, then `host.docker.internal`, `localhost`, the containerized `ollama:11434` (`apps/commonlib/commonlib/ollama_config.py`), and finally the LAN on port 11434 (see [Ollama server resolution](READMEs/AGENTIC_SDLC.md#network-discovery)). No module hard-depends on the `ollama` container, so it is never started implicitly.

```bash
# Ollama already installed on the host (nothing extra to start)
docker-compose --profile aienrich up -d aienrich

# Ollama containerized as well
docker-compose --profile ollama --profile aienrich up -d
```

### Install & run

Environment setup — Python/Node, host tools, dependencies, `.env` and `.env.secrets` — is documented once in [README_INSTALL.md](READMEs/README_INSTALL.md). After that:

```bash
docker-compose up -d      # core services
docker-compose logs -f

# in another terminal: the scrapper is not a Docker service
./apps/scrapper/run.sh    # or .\apps\scrapper\run.bat
```

Open the UI at [http://localhost:5173](http://localhost:5173). AI service profiles, the scrapper and Docker troubleshooting: [DOCKER_DEV.md](READMEs/DOCKER_DEV.md).

## Run Manually (Using Helper Scripts)

Each application includes convenience scripts (`run.sh` / `run.bat`) to start them easily.

### Linux / macOS (`.sh`)

```bash
# 1. Database
./scripts/runMysql.sh

# 2. Scrappers
./apps/scrapper/run.sh

# 3. AI Enrichment
# (Using Ollama, default, or OpenRouter with AI_ENRICH_BACKEND=openrouter)
./apps/aiEnrich/run.sh
# (Local Fast CV Matcher)
./apps/aiCvMatcher/run.sh
# (AI Form Filler backend)
./apps/aiFormFiller/run.sh

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
:: (Using Ollama, default, or OpenRouter with AI_ENRICH_BACKEND=openrouter)
.\apps\aiEnrich\run.bat
:: (Local Fast CV Matcher)
.\apps\aiCvMatcher\run.bat
:: (AI Form Filler backend)
.\apps\aiFormFiller\run.bat

:: 4. New UI (Backend + Web)
.\apps\backend\run.bat
.\apps\web\run.bat
```

## Developer tooling

Cross-cutting developer concerns are documented once, in the reference guides under [`READMEs/`](READMEs/):

- **Testing** (centralized runner, when to run the suites): [README_DEVELOPMENT.md#testing](READMEs/README_DEVELOPMENT.md#testing)
- **Static analysis** (Ruff, ESLint, `tsc`, pre-commit): [README_DEVELOPMENT.md#static-analysis](READMEs/README_DEVELOPMENT.md#static-analysis)
- **Coverage gates** (frontend union, scrapper statements): [README_DEVELOPMENT.md#coverage-gates](READMEs/README_DEVELOPMENT.md#coverage-gates)
- **Structured logging** (events, conventions, `LOG_*` config): [README_DEVELOPMENT.md#structured-logging](READMEs/README_DEVELOPMENT.md#structured-logging)
- **CodeGraph** (code intelligence) and agent skills, rules and guardrails: [AGENTIC_SDLC.md](READMEs/AGENTIC_SDLC.md)

## Documentation

- **Installation**: [README_INSTALL.md](READMEs/README_INSTALL.md)
- **Development**: [README_DEVELOPMENT.md](READMEs/README_DEVELOPMENT.md)
- **Contributing**: [README_CONTRIBUTE.md](READMEs/README_CONTRIBUTE.md)
- **Docker**: [DOCKER_DEV.md](READMEs/DOCKER_DEV.md)
- **GitHub Automation (CI & Dependabot)**: [README_GITHUB.md](READMEs/README_GITHUB.md)
- **Metrics & Grafana**: [README_METRICS.md](READMEs/README_METRICS.md)
- **Agentic SDLC** (agents, CodeGraph, guardrails): [AGENTIC_SDLC.md](READMEs/AGENTIC_SDLC.md)
