# Cron — Background Scheduler

Generic scheduler daemon that runs periodic cron jobs for background maintenance tasks.

## Tech Stack

Python 3.12, uv, pytest, MongoDB (`pymongo`), MySQL (`mysql-connector-python`)

## How it works

The scheduler runs in a loop, checking every 60s whether each registered job is due to run based on its cadency. Cadency is parsed from strings like `1h`, `30m`, `3600s`. Job state (last run, cursor position, error status) is persisted in MongoDB's `cron_state` collection.

On first tick after container restart, all jobs run immediately (ignoring cadency) so backfills start without waiting.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `MONGO_URI` | `mongodb://root:rootPass@localhost:27017/` | MongoDB URI |
| `MONGO_DATABASE` | `jobs` | MongoDB database name |
| `CRON_SALARY_CADENCY` | `1h` | Run interval for the salary history scanner |
| `COMMONLIB_DB_HOST` | `127.0.0.1` | MySQL host for job data |

## Registered jobs

- **companySalaryHistory** — Scans MySQL for new/updated job salaries and stores time-series data in MongoDB.

## Running

```bash
uv run cron
```

## Docker

Built from `Dockerfile` (Python 3.12-slim, uv-based). Runs via `docker-compose` as the `cron` service (auto-started).

## Testing

```bash
uv run pytest
uv run coverage run -m pytest && uv run coverage report -m
```
