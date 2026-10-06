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

Conventions: event names are dotted `domain.action` and never free text; dynamic values are `key=value` fields and no f-string is ever passed to a log call; `debug` is per-item detail, `info` is lifecycle, `warning` is recoverable, `exception` is a failed operation with its traceback. The CV is never logged - only its length and location - and neither are job descriptions or the embedding vectors. Neither module has a `print()` call. The wait between cycles in the main loop is `logIdleWait(cyan('All CV matches calculated.'), '10s', "jobs.skipped", reason="no_pending_jobs")`: it renders one record with that sentence as `message=` (plus `wait_seconds` and `reason`) and then waits on a `WakeableTimer`, so a container log shows one rendered line per cycle instead of a countdown nobody can see. On an interactive terminal it keeps the in-place countdown (`commonlib.terminalUtil.consoleTimer`), which is why `terminalColor.cyan` is still imported in `main.py`.

Each job is processed inside `job_log_context(id)` (`commonlib.observability`), so the `job.started` / `job.result` pair and every database record in between carry the same `job_id`.

`job.result` is a reserved name scraped by `commonlib.prometheus_exporter`, which requires both `job_id` and `duration`; the per-job `job.result` emitted here is debug-level detail and is not the exporter's metric.

### Configuration

| Variable | Default | Description |
|---|---|---|
| `AI_CVMATCHER_ENABLED` | — | Runs the match loop when true; `app.disabled` and exit otherwise |
| `AI_CVMATCHER_LIMIT` | `100` | Maximum jobs pulled per batch |
| `LOG_LEVEL` | `20` | 10=DEBUG, 20=INFO, 30=WARNING, 40=ERROR |
| `LOG_COLOR` | `True` | Colored console output instead of raw JSON on stdout |
| `LOG_DIR` | `data/logs` | Directory holding `aiCvMatcher.jsonl` |
| `LOG_FILE_MAX_BYTES` | `10485760` | Rotate the JSONL file once it grows past this |
| `LOG_FILE_BACKUP_COUNT` | `5` | Rotated files to keep |

These are shared with every other app; see [Structured Logging](../../READMEs/README_DEVELOPMENT.md#structured-logging) for the full reference.
