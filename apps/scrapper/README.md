# Job Scrappers

Automated job scraping service for multiple job boards (LinkedIn, Infojobs, Glassdoor, Tecnoempleo).

## Architecture

- **Navigators (`scrapper/navigator/`)**: Specialized classes that handle Selenium browser interactions for each site (e.g., `linkedinNavigator.py`, `infojobsNavigator.py`).
- **Services (`scrapper/services/`)**: Business logic and orchestration for job fetching and processing (e.g., `LinkedinService.py`, `InfojobsService.py`).
- **Coordinators**: Top-level scripts (`linkedin.py`, `infojobs.py`, etc.) that coordinate the scraping process.

## Features

- **Anti-Bot Measures**: Implements delays, mouse movements, and other techniques to mimic human behavior.
- **Undetected ChromeDriver**: Option to use `undetected-chromedriver` to bypass strict protections (Cloudflare).
- **Duplicate Management**: Automatically merges duplicate job listings (`mergeDuplicates.py` from `commonlib`).
- **Resilience**: Retry mechanisms for network failures and element loading issues.
- **Targeted validation errors**: `validate()` reports `job.field_invalid` only for the required fields that are actually empty, instead of flagging every field when a single one is missing.

## Supported Sites

- **LinkedIn**: Works fine. Careful with rate limits.
- **Infojobs**: Works fine.
- **Tecnoempleo**: Works fine. The company is read by `TecnoempleoCompanyReader`, which first tries the company link and then falls back to the bare text node tecnoempleo renders in the job header for the offers published without a company page. Only the offers that name no employer at all are stored with the company set to `unspecified` instead of being discarded, and the company is inferred later by `aiEnrich` (see [aiEnrich README](../aiEnrich/README.md)). While the company is unspecified the job is not linked to a duplicate; the duplicate check runs again once the company is known. The pay range is read by `TecnoempleoSalaryReader`, which matches the `Salario` caption of the "Datos principales" rows and stores the value in the `salary` column; offers stating no range are stored with `salary=NULL`. Matching the caption instead of a fixed row position matters because tecnoempleo renders a variable number of rows (`Imprescindible Residir`, `Otras Provincias` and `Salario` are all optional), and because the generic markdown scrape keeps the row values without their captions — the AI then receives the range as an unlabeled bullet and frequently answers `salary=null`. The page also exposes a schema.org `baseSalary` block, but it is missing on a noticeable share of salary-bearing offers, so it is not used.
- **Glassdoor**: Prone to strict bot detection. Uses Indeed OTP login (email+code via Gmail IMAP). `SCRAPPER_GLASSDOOR_EMAIL` is not used — GlassdoorAuthenticator reads `SCRAPPER_INDEED_EMAIL` instead.
- **Indeed**: Fully automated login with email+2FA support (Selenium). Alternatively, a Scrapling-based execution to bypass Cloudflare `StealthyFetcher` without login. Both paths read the redesigned viewjob DOM (Indeed moved the detail page to React Native Web markup): the current `data-testid` selectors are tried first and the legacy class-based selectors work as fallback, so title, company, location, description markdown, salary and the easy-apply flag keep working after the frontend rewrite.

## Dual Architecture (Selenium vs Scrapling)
The project initially relies heavily on Selenium + Undetected ChromeDriver. Recently, **Scrapling** framework has been introduced to bypass hard bot protections seamlessly, specifically Cloudflare Turnstiles.
Indeed scraper features a dual implementation:
- `IndeedExecutor`: Legacy architecture requiring Gmail/2FA login.
- `IndeedScraplingExecutor`: New architecture leveraging `scrapling` (`StealthyFetcher` + `ProxyRotator` + `solve_cloudflare=True`) to scrape jobs publicly without relying on authentication, which makes it faster and less error-prone when blocked. Controlled via `SCRAPPER_INDEED_SCRAPLING=true`.

Both implementations share the same selector strategy for the detail page (`vj-job-title`, `company-info-metadata`, `simple-job-description-html`, `viewjob-indeed-apply` first, previous markup second). Indeed also removed the SERP job-count pane, so `get_total_results` falls back to the `NN empleos` count in the page `<title>` when no count selector matches. The Scrapling session registers a `page_setup` callback that resizes the browser window through CDP (`Browser.setWindowBounds`) to the same geometry the Selenium path sets (1200 wide × `avail_height - 90`, right-aligned), so both implementations behave the same on screen.

## Setup & Running

### Prerequisites

See [README INSTALL](../../READMEs/README_INSTALL.md)

- Python 3.10+
- Google Chrome installed.
- Optional: [Gmail account](#gmail-configuration) with 2FA enabled for Indeed scraper.

### Installation

```bash
poetry install
```

`scrapling` is declared as `scrapling[fetchers]`: `scrapper/services/scrapling/scraplingService.py` imports `scrapling.fetchers`, and scrapling only declares that extra's runtime deps (`browserforge`, `apify-fingerprint-datapoints`, `protego`, `curl-cffi`, `playwright`, `patchright`, `msgspec`) behind the `fetchers` extra. Installing plain `scrapling` collects fine but crashes the test suite at import with `ModuleNotFoundError: No module named 'browserforge'`.

### Configuration

Scraper behavior is configured via environment variables and configuration files (`scrapper_config.py`).
See `.env` and `scripts/.env.secrets.example`.

## Key Environment Variables

- `SCRAPPER_USE_UNDETECTED_CHROMEDRIVER=true`: Enable undetected-chromedriver (Recommended for Infojobs/Glassdoor).
- `SCRAPPER_INDEED_EMAIL`: Indeed/Glassdoor login email (Glassdoor uses this for OTP login via Indeed popup).
- `GMAIL_EMAIL`: Gmail address for 2FA verification (Required for Indeed Selenium and Glassdoor OTP).
- `GMAIL_APP_PASSWORD`: 16-digit Gmail app password (Required for Indeed Selenium and Glassdoor OTP).
- `SCRAPPER_INDEED_SCRAPLING=true`: Switches execution of Indeed scraper to use the lightweight, Cloudflare-bypassing Scrapling implementation.
- `SCRAPPER_INDEED_PROXIES`: Comma delimited list of proxy servers for `ProxyRotator` (e.g., `http://username:pass@ip:port,http://...`).

## Specific Scraper Parameters

You can modify parameters in `scrapper/*.py` (e.g., `linkedin.py`):

```python
remote = '2'   # ["2"],  # onsite "1", remote "2", hybrid "3"
location = '105646813' # Spain (or other country code)
f_TPR = 'r86400'  # last 24 hours
DEBUG = False # Set to True to stop selenium driver on error
```

## Console Output & Structured Logging

The scrapper is the reference implementation of the dual-output logging in [Structured Logging](../../READMEs/README_DEVELOPMENT.md#structured-logging): the console is a human transcript and `apps/scrapper/data/logs/scrapper.jsonl` is the machine record.

`main.py` configures the app with `configure_logging("scrapper", console=CONSOLE_MESSAGE)`, so:

- A record with `console=` prints only that text — no timestamp, level, or event name — and the text is ANSI-stripped into the record's `message` in the JSONL.
- A record without `console=` is written to the JSONL only. This is what keeps `commonlib` chatter (`sql.query_executed`, `ollama.client.*`) off the console.
- `end=""` rebuilds a `print(..., end='')` progress prefix, so a job line such as `pg 1 job 1 - 42, Python Dev, Acme - INSERTED 99!` still assembles on one line. In JSONL each part is its own record.
- `LOG_CONSOLE_MODE` does not affect the scrapper: the mode is chosen in code, not from the environment.

The first line of every run is the resolved absolute path of the JSONL file, printed as a `logging.file_opened` record (with `path`), so the location is never a guess:

```text
Log file: /home/user/ai_job_search/apps/scrapper/data/logs/scrapper.jsonl
Scrapper v0.1.0
```

The path is resolved against the working directory of the process — `apps/scrapper` on the host, `/app` in the container — and honours `LOG_DIR`.

```python
logger.info("linkedin.job.scraped", job_id=job_id, title=title, company=company, easy_apply=easy,
            console=f"{job_id}, {title}, {cyan(company)}, {location}, easy_apply={easy} - ", end="")
logger.info("linkedin.job.inserted", job_id=job_id, insert_id=insert_id, console=green(f"INSERTED {insert_id}!"), end="")
logger.info("linkedin.job.duplicated", job_id=job_id, duplicated_id=duplicated_id, console=cyan(f" DUPLICATED {duplicated_id}"), end="")
```

Console text obeys the logging rules: OTP codes, email subjects, and URL query strings are never printed (only host + path, and `*_length` for codes), and `LinkedinService` prints the HTML/markdown lengths rather than the documents.

## Gmail Configuration

1. **Enable 2FA on Gmail**: Make sure 2FA is enabled on your Gmail account
2. **Generate App Password**:
   - Go to [Google Account settings](https://myaccount.google.com/security) → Security → 2-Step Verification → App passwords
    - or [Google Account settings](https://myaccount.google.com/apppasswords) 
   - Generate a 16-digit app password for this application
   - Use this password instead of your regular Gmail password

3. **Set Environment Variables**:
   ```bash
   GMAIL_EMAIL=your-gmail@gmail.com
   GMAIL_APP_PASSWORD=your-16-digit-app-password
   SCRAPPER_INDEED_EMAIL=your-indeed-email@example.com  
   ```

> **Note**: Changing these could cause violation of LinkedIn rate limits.

### Scheduling & Cadency

You can configure the run frequency for each scrapper using environment variables. 
The format is `XX_RUN_CADENCY=duration` (e.g., `1h`, `30m`).

## Dynamic Cadency (Time-based)
You can override the cadency for specific hours of the day.

Format: `XX_RUN_CADENCY_START-END=duration`

See `.env` and `scripts/.env.secrets.example` for examples.

Order of precedence:
1. Specific hour range match
2. Default environment variable (`XX_RUN_CADENCY`)
3. Hardcoded default


### Running Scrapers

**Automatic Loop Scraper:**

In AI-job-search root folder:
```bash
./apps/scrapper/run.sh # Linux/Mac
# or
.\apps\scrapper\run.bat # Windows
```

This runs an infinite loop checking for new jobs based on configured intervals.

**Run Specific Scraper:**

You can run individual scrapers manually:

```bash
.\apps\scrapper\run.bat linkedin
.\apps\scrapper\run.bat infojobs
```

**Run Single Job URL:**

Implemented for LinkedIn only:

```bash
.\apps\scrapper\run.bat url <job_url>
```

## Testing

Run tests with the centralized script, from the repository root (`commonlib` is always included because it holds the architecture tests):

```bash
./scripts/test.sh commonlib scrapper   # Linux/Mac
.\scripts\test.bat commonlib scrapper   # Windows
```

### Coverage

Tests live inside the package, so `[tool.coverage.run] omit` keeps `*/test/*` and
`*/conftest.py` out of the denominator. Without it, near-perfectly covered test files
were measured as production code and inflated the badge by ~8.8 points (80.8% real).

`fail_under` is intentionally **not** set in `pyproject.toml`: coverage.py only compares
the branch-inclusive total, and the project gates statements and lines only. The 90%
floor is enforced by `scripts/coverage/scrapper_coverage_gate.py`, which `scripts/test.sh`
and `scripts/test.bat` run automatically in `--coverage` mode:

```bash
cd apps/scrapper
poetry run coverage run -m pytest
poetry run coverage xml
python ../../scripts/coverage/scrapper_coverage_gate.py --min 90
```

It exits non-zero when production statements drop below the floor and lists the
least-covered files. Branch coverage stays enabled for information only.

## Troubleshooting

- **Rate Limits**: If you get 429 errors or captchas, increase delays or stop scraping for a while.
- **ARSF (Anti Robot Security Filters)**: If Chrome opens but gets blocked, try `SCRAPPER_USE_UNDETECTED_CHROMEDRIVER=true` or use a VPN.
- **Gmail Issues**: Ensure app password is correctly generated and 2FA is enabled.
- **2FA Timeout**: Increase timeout in GmailService if verification emails are slow to arrive.
