# AI job search

[![backend-build-lint-and-tests](https://github.com/davidgfolch/AI-job-search/actions/workflows/python-app.yml/badge.svg)](https://github.com/davidgfolch/AI-job-search/actions/workflows/python-app.yml)

| Module's coverage    |                                               | UI Module's coverage |                                      |
|----------------------|-----------------------------------------------|----------------------|--------------------------------------|
| packages/commonlib   | ![commonlib](packages/commonlib/coverage.svg) | apps/viewer (old UI) | ![viewer](apps/viewer/coverage.svg)  |
| apps/aiEnrich        | ![aiEnrich](apps/aiEnrich/coverage.svg)       | apps/web (new UI)    | ![web](apps/web/coverage/badges.svg) |
| apps/scrapper        | ![scrapper](apps/scrapper/coverage.svg)       | apps/backend (new UI)    | ![backend](apps/backend/coverage.svg)        |



Application to search & find jobs, scrappers for LinkedIn, Infojobs, Glassdoor, Tecnoempleo...

- Selenium sites scrappers to store in local mysql database.
- Artificial intelligence to enrich the job offer with structured information (salary, required technologies, ...).
- User interface to filter, see, manage & clean jobs in database.

## Setup

See [README_INSTALL.md](./READMEs/README_INSTALL.md)

## Run with Docker (Development Mode) 🐳

The easiest way to run all services in development mode is using Docker Compose:

```bash
# Start core services (MySQL + Backend + Web + Viewer)
docker-compose up -d

# View logs
docker-compose logs -f

# Access services:
# - Web UI: http://localhost:5173
# - Backend API: http://localhost:8000/docs
# - Viewer (Streamlit): http://localhost:8501
```

**Optional services:**
```bash
# With AI enrichment (includes Ollama)
docker-compose --profile ai-services up -d

# With scrapper (NOT WORKING IN WINDOWS)
docker-compose --profile scrapper up -d scrapper

# All services  (NOT WORKING IN WINDOWS)
docker-compose --profile ai-services --profile scrapper up -d
```

See [DOCKER_DEV.md](./DOCKER_DEV.md) for detailed Docker commands and troubleshooting.

## Run & lifecycle (Without Docker)

Run scripts in separate terminals.

### Linux

```bash
# Start mysql with docker compose
./scripts/run_1_Mysql.sh
# Start all scrappers (follow browser & console to solve robot security filters)
./apps/scrapper/run.sh  # or
./apps/scrapper/run.sh Linkedin Infojobs Glassdoor  # Run specific scrappers
# OPTIONAL: Process each job offer with AI/LLM inference in database, extracting salary, required technologies, etc...
./apps/aiEnrich/run.sh
# Run User interface to edit
./apps/viewer/run.sh
```

### Windows

```shell
docker compose up -d  # Start mysql with docker compose
# Start all scrappers (follow browser & console to solve robot security filters)
.\apps\scrapper\run.bat
# OPTIONAL: Process each job offer with AI/LLM inference in database, extracting salary, required technologies, etc...
.\apps\aiEnrich\run.bat
.\apps\viewer\run.bat
```

## Scrapers

The automatic scrapper (`./apps/scrapper/run.sh` without parameters) keeps running in a infinite loop in console.  Different timeouts are configured in `scrapper/main.py` for each site scrapper.

See [module README.md](apps/scrapper/README.md)

## AI enricher (optional)

This will use LLM to extract structured data from job offers (salary, required_technologies, ...).  Using CrewAI framework & local Ollama LLM.

The automatic script `./apps/aiEnrich/run.sh` keeps running in a infinite loop in console, waiting for jobs not `ai_enriched` in database.

## Viewer

User interface available to see & manage jobs with many capabilities:

- **View & manage** tab:
  - Search jobs using the filter form:
    - Configurable defaults saved to local storage files (`.stSessionState`).
    - Select one (or more) in search results to edit.
      - Add comments in each offer in interviews or calls.
      - Change states (ignored, seen, applied, closed, discarded, etc.)
- **Clean** tab:
  - Set some expressions to select jobs offers to be automatically ignored.
  - Delete old job offers from database.
- **Statistics** tab.

## Contribute

[See README_CONTRIBUTE.md](READMEs/README_CONTRIBUTE.md)
