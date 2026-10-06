# aiEnrich3
CPU-optimized multilingual data extraction service for job offers using GLiNER, mDeBERTa, and Regex.

## Logs
Structured logging via `commonlib.observability`; records go to stdout and are mirrored to `data/logs/aiEnrich3.jsonl`. Each job is processed inside `job_log_context(id)`, so its `job.started` / `job.result` pair and every database record in between carry the same `job_id`. The wait between cycles in the main loop is `logIdleWait(cyan('All jobs enriched.'), '10s', "jobs.skipped", reason="no_pending_jobs")`: one record carrying that sentence as `message=`, then a `WakeableTimer` (interactive terminals keep the in-place countdown). See [Structured Logging](../../READMEs/README_DEVELOPMENT.md#structured-logging).