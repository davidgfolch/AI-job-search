# Cron — Background Scheduler

Generic scheduler daemon that runs periodic cron jobs for background maintenance tasks.

## Tech Stack

Python 3.12, uv, pytest, MongoDB (`pymongo`), MySQL (`mysql-connector-python`)

## How it works

The scheduler runs in a loop, checking every 60s whether each registered job is due to run based on its cadency. Cadency is parsed from strings like `1h`, `30m`, `3600s`. Job state (last run, cursor position, error status) is persisted in MongoDB's `cron_state` collection.

On first tick after container restart, all jobs run immediately (ignoring cadency) so backfills start without waiting.

## Structured logging

Telemetry goes through `commonlib.observability` instead of `print()`. `run()` calls `configure_logging("cron")` as its first statement, before the Mongo provider is built, because `structlog` freezes the level on the first log call; every module then binds a logger at module level:

```python
logger = get_logger("cron.scheduler")
logger.info("cron.job_started", job=job.name)
```

Console output goes to stdout and every record is mirrored to a JSONL file, one JSON object per line, at `data/logs/cron.jsonl` relative to the working directory — `apps/cron/data/logs/cron.jsonl` on the host, since the container mounts the app directory.

| Module | Events |
|---|---|
| `main` | `cron.started`, `cron.jobs_registered` (info); `cron.tick` (info); `cron.job_registered` (debug, one per job) |
| `scheduler` | `cron.job_started`, `cron.job_completed` (info); `cron.job_failed` (exception — records the traceback, the job name and the error message) |
| `jobs/company_salary_history/job` | `cron.scan_started`, `cron.scan_completed` (info); `cron.scan_no_records` (debug) |
| `jobs/company_salary_history/scanner` | `cron.scanner.jobs_fetched`, `cron.scanner.records_saved`, `cron.scanner.updates_checked`, `cron.scanner.updates_saved` (info); `cron.scanner.no_new_jobs`, `cron.scanner.salary_recorded` (debug, one per changed job) |

Conventions: event names are dotted `domain.action` and never free text; dynamic values are `key=value` fields and no f-string is ever passed to a log call; `debug` is per-item detail, `info` is lifecycle, `exception` is a failed operation with its traceback. Mongo URIs and other env values are never logged — only derived counts, cadencies and job ids. Nothing in this app is presentational output, so no `print()` remains.

`cron.job_failed` is the event to alert on: job failures are recorded at `error` level and the scheduler still persists `status=error` in `cron_state`, so the job is retried on the next tick.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `MONGO_URI` | `mongodb://root:rootPass@localhost:27017/` | MongoDB URI |
| `MONGO_DATABASE` | `jobs` | MongoDB database name |
| `CRON_SALARY_CADENCY` | `1h` | Run interval for the salary history scanner |
| `COMMONLIB_DB_HOST` | `127.0.0.1` | MySQL host for job data |
| `LOG_LEVEL` | `20` | 10=DEBUG, 20=INFO, 30=WARNING, 40=ERROR |
| `LOG_COLOR` | `True` | Colored console output instead of raw JSON on stdout |
| `LOG_DIR` | `data/logs` | Directory holding `cron.jsonl` |
| `LOG_FILE_MAX_BYTES` | `10485760` | Rotate the JSONL file once it grows past this |
| `LOG_FILE_BACKUP_COUNT` | `5` | Rotated files to keep |

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
