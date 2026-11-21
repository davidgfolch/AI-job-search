# Cron — Background Scheduler

Generic scheduler daemon that runs periodic cron jobs for background maintenance tasks.

## Tech Stack

Python 3.12, uv, pytest, MongoDB (`pymongo`), MySQL (`mysql-connector-python`)

## How it works

The scheduler runs in a loop, checking whether each registered job is due to run based on its cadency.

On first tick after container restart, all jobs run immediately (ignoring cadency) so backfills start without waiting. Failed jobs are retried on the next tick.

## Structured logging

Telemetry goes through `commonlib.observability`; see [Structured Logging](../../READMEs/README_DEVELOPMENT.md#structured-logging) for event conventions and output layout.
Mongo URIs and other env values are never logged.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `MONGO_URI` | `mongodb://root:rootPass@localhost:27017/` | MongoDB URI |
| `MONGO_DATABASE` | `jobs` | MongoDB database name |
| `CRON_SALARY_CADENCY` | `1h` | Run interval for the salary history scanner; accepts `1h`, `30m`, `3600s` |
| `COMMONLIB_DB_HOST` | `127.0.0.1` | MySQL host for job data |

Shared `LOG_*` variables are documented in [Structured Logging](../../READMEs/README_DEVELOPMENT.md#structured-logging).

## Registered jobs

- **companySalaryHistory** — Scans MySQL for new/updated job salaries and stores time-series data in MongoDB.

## Running

```bash
# From the repository root
./apps/cron/run.sh    # Linux/Mac
.\apps\cron\run.bat   # Windows
```

Dependencies are installed by the centralized installer (`./scripts/install.sh` / `.\scripts\install.bat`); see [Setup Guide](../../READMEs/README_INSTALL.md).

## Docker

Built from `Dockerfile` (Python 3.12-slim, uv-based). Runs via `docker-compose` as the `cron` service (auto-started).

## Testing

```bash
./scripts/test.sh commonlib cron   # Linux/Mac
.\scripts\test.bat commonlib cron  # Windows

# With coverage
./scripts/test.sh --coverage commonlib cron
```
