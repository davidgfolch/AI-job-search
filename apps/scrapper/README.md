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

## Supported Sites

- **LinkedIn**: Works fine. Careful with rate limits.
- **Infojobs**: Works fine.
- **Tecnoempleo**: Works fine.
- **Glassdoor**: Prone to strict bot detection.
- **Indeed**: Fully automated login with email+2FA support. Requires Gmail setup.

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

### Configuration

Scraper behavior is configured via environment variables and configuration files (`scrapper_config.py`).
See `scripts/.env.example`.

## Key Environment Variables

- `USE_UNDETECTED_CHROMEDRIVER=true`: Enable undetected-chromedriver (Recommended for Infojobs/Glassdoor).
- `GMAIL_EMAIL`: Gmail address for 2FA verification (Required for Indeed).
- `GMAIL_APP_PASSWORD`: 16-digit Gmail app password (Required for Indeed).

## Specific Scraper Parameters

You can modify parameters in `scrapper/*.py` (e.g., `linkedin.py`):

```python
remote = '2'   # ["2"],  # onsite "1", remote "2", hybrid "3"
location = '105646813' # Spain (or other country code)
f_TPR = 'r86400'  # last 24 hours
DEBUG = False # Set to True to stop selenium driver on error
```

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
   INDEED_EMAIL=your-indeed-email@example.com  
   ```

> **Note**: Changing these could cause violation of LinkedIn rate limits.

### Scheduling & Cadency

You can configure the run frequency for each scrapper using environment variables. 
The format is `XX_RUN_CADENCY=duration` (e.g., `1h`, `30m`).

## Dynamic Cadency (Time-based)
You can override the cadency for specific hours of the day.

Format: `XX_RUN_CADENCY_START-END=duration`

See `scripts/.env.example` for examples.

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

Run tests with pytest:

```bash
poetry run pytest
```

## Troubleshooting

- **Rate Limits**: If you get 429 errors or captchas, increase delays or stop scraping for a while.
- **ARSF (Anti Robot Security Filters)**: If Chrome opens but gets blocked, try `USE_UNDETECTED_CHROMEDRIVER=true` or use a VPN.
- **Gmail Issues**: Ensure app password is correctly generated and 2FA is enabled.
- **2FA Timeout**: Increase timeout in GmailService if verification emails are slow to arrive.
