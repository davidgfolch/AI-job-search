# Job Scrappers

Automated job scraping service for multiple job boards (LinkedIn, Infojobs, Glassdoor, Tecnoempleo).

## Architecture

Refactored to a modular architecture:

- **Navigators (`scrapper/navigator/`)**: Specialized classes that handle Selenium browser interactions for each site (e.g., `linkedinNavigator.py`, `infojobsNavigator.py`).
- **Services (`scrapper/services/`)**: Business logic and orchestration for job fetching and processing (e.g., `LinkedinService.py`, `InfojobsService.py`).
- **Coordinators**: Top-level scripts (`linkedin.py`, `infojobs.py`, etc.) that coordinate the scraping process.

## Features

- **Anti-Bot Measures**: Implements delays, mouse movements, and other techniques to mimic human behavior.
- **Undetected ChromeDriver**: Option to use `undetected-chromedriver` to bypass strict protections (Cloudflare).
- **Duplicate Management**: Automatically merges duplicate job listings (`mergeDuplicates.py` from `commonlib`).
- **Resilience**: Retry mechanisms for network failures and element loading issues.

## Supported Sites

- **LinkedIn**: Works fine. Careful with rate limits.
- **Infojobs**: Works fine.
- **Tecnoempleo**: Works fine.
- **Glassdoor**: Prone to strict bot detection.

## Setup & Running

### Prerequisites

- Python 3.10+
- Google Chrome installed.

### Installation

```bash
poetry install
```

### Configuration

Scraper behavior is configured via environment variables and configuration files (`scrapper_config.py`).
See `.env.example` in `scripts/`.

**Key Environment Variables:**

- `USE_UNDETECTED_CHROMEDRIVER=true`: Enable undetected-chromedriver (Recommended for Infojobs/Glassdoor).

**Specific Scraper Parameters:**
You can modify parameters in `scrapper/*.py` (e.g., `linkedin.py`):

```python
remote = '2'   # ["2"],  # onsite "1", remote "2", hybrid "3"
location = '105646813' # Spain (or other country code)
f_TPR = 'r86400'  # last 24 hours
DEBUG = False # Set to True to stop selenium driver on error
```

> **Note**: Changing these could cause violation of LinkedIn rate limits.

### Running Scrapers

**Automatic Loop Scraper:**

```bash
./run_2_Scrapper.sh # Linux/Mac
# or
.\run.bat # Windows
```

This runs an infinite loop checking for new jobs based on configured intervals.

**Run Specific Scraper:**

You can run individual scrapers manually:

```bash
poetry run python scrapper/linkedin.py
poetry run python scrapper/infojobs.py
```

**Run Single Job URL (LinkedIn):**

```bash
poetry run python scrapper/linkedin.py url <job_url>
```

## Testing

Run tests with pytest:

```bash
poetry run pytest
```

## Troubleshooting

- **Rate Limits**: If you get 429 errors or captchas, increase delays or stop scraping for a while.
- **ARSF (Anti Robot Security Filters)**: If Chrome opens but gets blocked, try `USE_UNDETECTED_CHROMEDRIVER=true` or use a VPN.
