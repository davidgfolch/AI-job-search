# [![backend-build-lint-and-tests](https://github.com/davidgfolch/AI-job-search/actions/workflows/python-app.yml/badge.svg)](https://github.com/davidgfolch/AI-job-search/actions/workflows/python-app.yml) [![Backend coverage](READMEs/img/coverage.svg)](README.md#generate-coverage-badge-for-readmemd)

Application to search & find jobs, scrappers for LinkedIn, Infojobs, Glassdoor, Tecnoempleo...

- Selenium sites scrappers to store in local mysql database.
- (OPTIONAL) Artificial intelligence to enrich the job offer with structured information (salary, required technologies, ...). You will need a local Ollama installation, [see setup](#setup).
- User interface to filter, see, manage & clean jobs in database.

## Setup

See [README_INSTALL.md](./READMEs/README_INSTALL.md)

## Run & lifecycle

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

### Run all with single bash script

Alternatively if you have terminator installed you can run all in one with: `./run.sh`

NOTE that to execute `run.sh` you will need:

- Perl installed and `colorTail.pl` script to be available in your `~/scripts/` folder
- or remove `| perl ~/scripts/colorTail.pl \"gpu|cuda\"` in `run.sh` command line pipe for Ollama logs

## Scrapers

The automatic scrapper (`./run_2_Scrapper.sh` without parameters) keeps running in a infinite loop in console.  Different timeouts are configured in `scrapper.py` for each site scrapper.

See [README_SCRAPPERS.md](READMEs/README_SCRAPPERS.md)

## AI enricher (optional)

This will use LLM to extract structured data from job offers (salary, required_technologies, ...).  Using CrewAI framework & local Ollama LLM.

The automatic script `./scripts/run_3_AiEnricher.sh` keeps running in a infinite loop in console, waiting for jobs not `ai_enriched` in database.

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
