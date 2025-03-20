# AI Job Search

[![backend-build-lint-and-tests](https://github.com/davidgfolch/AI-job-search/actions/workflows/python-app.yml/badge.svg)](https://github.com/davidgfolch/AI-job-search/actions/workflows/python-app.yml)
[![Backend coverage](READMEs/img/coverage.svg)](README.md#generate-coverage-badge-for-readmemd)

Application to search & find jobs, scrappers for LinkedIn, Infojobs, Glassdoor, Tecnoempleo...

- Selenium sites scrappers to store in local mysql database.
  - Be aware of Anti Robot Security Filters (**ARSF**)
    - LinkedIn works fine.
    - Infojobs works fine, but it will show **ARSF** at the beginning of scrape.
    - Glassdoor could show **ARSF** "all the time", scrapper just re-run selenium browser on error.
    - Tecnoempleo works fine.
    - ~~Indeed **ARSF** all the time (DISABLED)~~
- OPTIONAL: Artificial intelligence to enrich the job offer with structured information (salary, required technologies, ...).
  - You will need a [local Ollama installation](https://github.com/davidgfolch/OpenAI-local-ollama-chat/blob/main/README_OLLAMA.md).
- User interface to see, organize, edit & clean jobs in database

## Setup

See [README_INSTALL.md](./READMEs/README_INSTALL.md)

## Lifecycle

Run bash scripts in separate terminals:

```bash
# Start mysql with docker compose
./scripts/run_1_Mysql.sh
# Start all scrappers (follow browser & console to solve robot security filters)
./scripts/run_2_Scrapper.sh  # or
./scripts/run_2_scrapper.sh Linkedin Infojobs Glassdoor  # Run specific scrappers
# OPTIONAL: Process each job offer with AI/LLM inference in database, extracting salary, required technologies, etc...
./scripts/run_3_AiEnricher.sh
# Run User interface to edit
./scripts/run_4_Viewer.sh
```

## Scrapers

The automatic scrapper (`./run_2_Scrapper.sh` without parameters) keeps running in a infinite loop in console.  Different timeouts are configured in `scrapper.py` for each site scrapper.

[See README_SCRAPPERS.md](READMEs/README_SCRAPPERS.md)

## AI enricher (optional)

This will use LLM to extract structured data from job offers (salary, required_technologies, ...).  Using CrewAI framework & local Ollama LLM.

The automatic script `./scripts/run_3_AiEnricher.sh` keeps running in a infinite loop in console, waiting for jobs not `ai_enriched` in database.

## Contribute

[See README_CONTRIBUTE.md](READMEs/README_CONTRIBUTE.md)
