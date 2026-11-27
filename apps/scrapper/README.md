# Job Scrappers

Automated job scraping service for multiple job boards (LinkedIn, Infojobs, Glassdoor, Tecnoempleo).

## Architecture

The scrapper separates browser navigation, site-specific job fetching and per-site executors; top-level scripts coordinate each platform.

## Features

- **Anti-bot handling**: Optional undetected ChromeDriver for strict protections.
- **Duplicate management**: Duplicate job listings are merged automatically.
- **Resilience**: Transient network and page-loading failures are retried.

## Supported Sites

- **LinkedIn**: Works fine. Careful with rate limits.
- **Infojobs**: Works fine.
- **Tecnoempleo**: Works fine. Offers without a company name are kept as `unspecified` and resolved later by `aiEnrich`; a stated salary range is stored in the `salary` column.
- **Glassdoor**: Prone to strict bot detection. Uses Indeed OTP login (email+code via Gmail IMAP) with `SCRAPPER_INDEED_EMAIL`.
- **Indeed**: Automated login with email+2FA, or a Scrapling path that bypasses Cloudflare without login (`SCRAPPER_INDEED_SCRAPLING=true`). Offers whose page is gone or broken are skipped.

## Setup & Running

### Prerequisites

See [README INSTALL](../../READMEs/README_INSTALL.md)

- Python 3.11+
- Google Chrome installed.
- Optional: [Gmail account](#gmail-configuration) with 2FA enabled for Indeed scraper.

### Installation

From the repository root:

```bash
./scripts/install.sh    # Linux/Mac
.\scripts\install.bat   # Windows
```

### Running

From the repository root (pass a platform to run only that site, or `url <job_url>` to scrape one LinkedIn job):

```bash
./apps/scrapper/run.sh    # Linux/Mac
.\apps\scrapper\run.bat   # Windows
```

### Configuration

Scraper behavior is configured via environment variables and configuration files (`scrapper_config.py`).
See `.env` and `scripts/.env.secrets.example`.

## Key Environment Variables

- `SCRAPPER_JOBS_SEARCH`: Comma-separated job search terms.
- `SCRAPPER_USE_UNDETECTED_CHROMEDRIVER=true`: Enable undetected ChromeDriver (recommended for Infojobs/Glassdoor).
- `SCRAPPER_INDEED_EMAIL`: Indeed/Glassdoor login email.
- `GMAIL_EMAIL`: Gmail address for 2FA verification (required for Indeed and Glassdoor OTP).
- `GMAIL_APP_PASSWORD`: 16-digit Gmail app password (required for Indeed and Glassdoor OTP).
- `SCRAPPER_INDEED_SCRAPLING=true`: Use the Cloudflare-bypassing Scrapling implementation for Indeed.
- `SCRAPPER_INDEED_PROXIES`: Comma-separated proxy list (e.g., `http://username:pass@ip:port,http://...`).
- `SCRAPPER_LINKEDIN_QUERY_MODE`: `keywords` (default) uses plain search terms; `ai` uses a natural-language remote query (higher remote precision, lower recall).
- `SCRAPPER_LINKEDIN_AI_QUERY_SUFFIX`: query appended in `ai` mode (default `100% remoto dentro de España`).

## Console Output & Structured Logging

The scrapper writes progress to the console and structured records to `apps/scrapper/data/logs/scrapper.jsonl`.
Shared conventions are documented in [Structured Logging](../../READMEs/README_DEVELOPMENT.md#structured-logging).
The web statistics chart uses these records for per-keyword counts.

Run the local per-keyword report from the repository root:

```bash
python scripts/scrapper_keyword_stats.py --days 7 --site Indeed --keyword python --csv /tmp/keywords.csv
```

`--date YYYY-MM-DD`, `--max-ids N` and `--log-dir` are also supported. The report warns when log rotation has removed older dates.
Remote scrappers send the same records to the backend; see [Distributed execution](../../READMEs/DISTRIBUTED_EXECUTION.md#scrapper-logs-on-a-remote-backend).

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

### Dynamic Cadency (Time-based)

You can override the cadency for specific hours of the day.

Format: `XX_RUN_CADENCY_START-END=duration`

See `.env` and `scripts/.env.secrets.example` for examples.

Order of precedence:
1. Specific hour range match
2. Default environment variable (`XX_RUN_CADENCY`)
3. Hardcoded default

### Keyword Resume

Scrappers resume from their last processed keyword after a restart and retry keywords that failed previously.

## Testing

Run tests with the centralized script, from the repository root (`commonlib` is always included because it holds the architecture tests):

```bash
./scripts/test.sh commonlib scrapper   # Linux/Mac
.\scripts\test.bat commonlib scrapper   # Windows
```

### Coverage

Run the 90% statements/lines gate through the centralized runner:

```bash
./scripts/test.sh --coverage commonlib scrapper   # Linux/Mac
.\scripts\test.bat --coverage commonlib scrapper  # Windows
```

## Troubleshooting

- **Rate Limits**: If you get 429 errors or captchas, increase delays or stop scraping for a while.
- **ARSF (Anti Robot Security Filters)**: If Chrome opens but gets blocked, try `SCRAPPER_USE_UNDETECTED_CHROMEDRIVER=true` or use a VPN.
- **Gmail Issues**: Ensure app password is correctly generated and 2FA is enabled.
- **2FA Timeout**: Increase timeout in GmailService if verification emails are slow to arrive.
