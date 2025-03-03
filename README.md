# AI Job Search

[![backend-build-lint-and-tests](https://github.com/davidgfolch/AI-job-search/actions/workflows/python-app.yml/badge.svg)](https://github.com/davidgfolch/AI-job-search/actions/workflows/python-app.yml)
[![Backend coverage](README-images/coverage.svg)](backend/README.md#generate-coverage-badge-for-readmemd)

Application to search & find jobs, scrappers for LinkedIn, Infojobs, Glassdoor, Tecnoempleo...

- Selenium sites scrappers to store in local database.
  - Be aware of Anti Robot Security Filters (**ARSF**)
    - LinkedIn works fine.
    - Infojobs works fine, but it will show **ARSF** at the beginning of scrape.
    - Glassdoor could show **ARSF** "all the time", just re-run
    - Tecnoempleo works fine.
    - Indeed **ARSF** all the time (DISABLED)
- OPTIONAL: Artificial intelligence to enrich the job offer with structured information (salary, required technologies, ...).
  - You will need a [local Ollama installation](https://github.com/davidgfolch/OpenAI-local-ollama-chat/blob/main/README_OLLAMA.md).
- User interface to see, organize, edit & clean jobs in database

## Prerequisites

- [Docker & docker-compose](https://docs.docker.com/compose/install/)
- [Local Ollama](https://github.com/davidgfolch/OpenAI-local-ollama-chat/blob/main/README_OLLAMA.md) (OPTIONAL)
- Python 3.11 & libraries, see  [README_INSTALL.md](./README_INSTALL.md)

## Setup

Setup credentials & other settings in `.env` file. You have an `.env.example` you can copy:

```bash
cp .env.example .env
```

Then edit your `.env` file.

> NOTE: AiEnricher using OPENAI_API_KEY or GEMINI_API_KEY is not tested.

## Lifecycle

Run bash scripts in separate terminals:

```bash
# Start mysql with docker compose
./run_1_Mysql.sh

# Start all scrappers (follow browser & console to solve robot security filters)
./run_2_Scrapper.sh
./run_2_scrapper.sh Linkedin Infojobs Glassdoor  # Run specific scrappers

# OPTIONAL: Process each job offer with AI/LLM inference in database, extracting salary, required technologies, etc...
./run_3_AiEnricher.sh

# Run User interface to edit
./run_4_Viewer.sh
# OPTIONAL: Find salary ranges for company/role in Glassdoor
./run_5_ScrapperEnricher.sh
```

### Clean data (viewer)

Duplicated jobs will be created in database if the jobId is different, `./run_4_Viewer.sh` & click on `Clean data` button to merge old jobs states & comments into the last one (grouping jobs by title-company) & deleting older ones.

> NOTE: is a good practice to Clean duplicated job offers before AiEnricher.

## Scrapers

The automatic scrapper (execution with no parameters) keeps running in a infinite loop in console.  Different timeouts can be configured in `scrapper.py`

To avoid RATE LIMITS security filters, job search's are limited to last 24 hours only (sorting newest first), so scrappers must run each day to not miss job offers.

| KNOWN PROBLEMS | Solution |
|--------|-------|
| Scrappers can fail randomly | Re-run |
| Scrappers could fail due to (random) anti-robot security filters or any other reason| Set `DEBUG=True` in the failing scrapper, re-run & solve security filter |

### Implementations

#### Linkedin

Rate limits: LinkedIn has rate limit even for authenticated users, so if you execute **`scrapper/linkedin.py`** several times or have too much `JOBS_SEARCH` keywords you will be spending LinkedIn rate limit.  If rate limit is exhausted all request will return a HTTP STATUS CODE = 429

After some days executing the selenium script we also found a security human check, so we have to pause execution after login and solve puzzle manually.

![alt text](README-images/LinkedInSecurityVerification.png)

#### Infojobs

Security filter will appear, you'll need to solve it manually & press a key in the terminal

#### Glassdoor

Security filter will appear, you'll need to solve it manually.

#### Other parameters

There are other parameters you can change in **`scrapper/*.py`**

For example for Linkedin:

```python
remote = '2'   # ["2"],  # onsite "1", remote "2", hybrid "3"
# Spain if you need other make a manual search and get your country code
location = '105646813'
f_TPR = 'r86400'  # last 24 hours
# Set to True to stop selenium driver navigating if any error occurs
DEBUG = False
```

> NOTE: changing those could cause violation of LinkedIn rate limit

## AI enricher (optional)

This will run LLM filling some extra fields from the job offer (salary, required_technologies, ...).  Using CrewAI framework (using local Ollama LLM by default).

The automatic bash script keeps running in a infinite loop in console, waiting for jobs not `ai_enriched` in database.  Automatic jobs merge is executed before enrichment to save inference time, it merges the ai enriched structured data for same job `title` and `company`.

## Tests & coverage

```bash
# run tests
python -m pytest 
# run coverage
coverage run --source=src -m pytest 
coverage report -m
# see coverage
coverage html
```

All in one:

```bash
pytest && coverage run --source=src -m pytest && coverage report -m
```

## Generate coverage badge for README.md

```bash
cd backend
coverage-badge -o ../README.md_images/coverage.svg -f
```

NOTE: pipeline generation don't work
