# AI CV Matcher

This module handles fast CV matching against job descriptions using local Hugging Face embedding models (`sentence-transformers`). It acts as a dedicated microservice that continuously polls the database for pending CV matches if `AI_CVMATCHER_ENABLED` is enabled in the environment.

## Requirements

- Python >= 3.10
- MySQL Database (Shared within monorepo)
- `uv` package manager

## Quickstart

Configure `.env` with:
```env
AI_CVMATCHER_ENABLED=True
AI_CVMATCHER_LIMIT=100
```
Then run via Docker:
```bash
docker-compose up -d aicvmatcher
```

Or manually:
```bash
cd apps/aiCvMatcher
uv run aicvmatcher
```

## Structured logging

Telemetry goes through `commonlib.observability` instead of `print()`. `run()` calls `configure_logging("aiCvMatcher")` as its first statement, before the model is built, because `structlog` freezes the level on the first log call; every module then binds a logger at module level:

```python
logger = get_logger("aiCvMatcher.cvMatcher")
logger.info("jobs.batch_started", total=total, limit=limit, count=len(job_ids))
```

Console output goes to stdout and every record is mirrored to a JSONL file, one JSON object per line, at `data/logs/aiCvMatcher.jsonl` relative to the working directory - `apps/aiCvMatcher/data/logs/aiCvMatcher.jsonl` on the host. The backend container mounts that directory read-only at `/logs/aicvmatcher` and its dashboard reads the file to show recent errors and last activity, so the records below are a contract with the UI.

| Module | Events |
|---|---|
| `main` | `app.started` (info); `app.disabled` (info, with the `flag` that turned the worker off); `jobs.skipped` (info, `message='All CV matches calculated.'`, plus `wait_seconds` and `reason`) |
| `cvMatcher` | `model.loading`, `model.loaded`, `cv.context_loaded`, `jobs.batch_started`, `jobs.batch_completed` (info); `job.started`, `job.result` (debug, one per job); `job.error_saved` (warning, the match percentage is set to `-1`); `match.failed` (exception - records the traceback); `job.failed` (exception - records the traceback, the job id, title and company); `jobs.batch_errors` (warning, count of failures in the run) |

The CV is never logged - only its length and location - and neither are job descriptions or the embedding vectors. Each job runs inside `job_log_context(id)`, so its records carry the same `job_id`. The idle wait uses `logIdleWait()` (one `jobs.skipped` record on a `WakeableTimer`) instead of a countdown. `job.result` here is debug detail, not the exporter's metric of the same name. Event names, levels, and the shared `LOG_*` variables are documented once in [Structured Logging](../../READMEs/README_DEVELOPMENT.md#structured-logging).

### Configuration

| Variable | Default | Description |
|---|---|---|
| `AI_CVMATCHER_ENABLED` | — | Runs the match loop when true; `app.disabled` and exit otherwise |
| `AI_CVMATCHER_LIMIT` | `100` | Maximum jobs pulled per batch |
