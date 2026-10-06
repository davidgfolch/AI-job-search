# aiEnrichNew

This module performs AI-based enrichment of job data (extracting technologies, salary, modality, etc.) using **local Hugging Face models** directly via the `transformers` library.

It is designed to be a lightweight, free alternative to the `aiEnrich` module (which uses Ollama).

## Prerequisites

- [uv](https://github.com/astral-sh/uv) installed.
- A GPU is recommended for faster inference, but CPU works (slower).

## Usage

### Windows
```cmd
run.bat
```

### Linux / Mac
```bash
./run.sh
```

### Manual
```bash
# Run
uv run aienrichnew
```

## Configuration

- **Model**: Defaults to `Qwen/Qwen2.5-1.5B-Instruct` (defined in `src/aiEnrichNew/dataExtractor.py`).
- **Environment Variables**:
    - `AI_ENRICHNEW_EXTRACT_TIMEOUT_SECONDS`: (Optional) Timeout for extraction.

## Logs

Structured logging via `commonlib.observability`; records go to stdout and are mirrored to `data/logs/aiEnrichNew.jsonl`. Each job is processed inside `job_log_context(id)`, so its `job.started` / `job.result` pair and every database record in between carry the same `job_id`. The wait between cycles in the main loop is `logIdleWait(cyan('All jobs enriched.'), '10s', "jobs.skipped", reason="no_pending_jobs")`: one record carrying that sentence as `message=`, then a `WakeableTimer` (interactive terminals keep the in-place countdown). See [Structured Logging](../../READMEs/README_DEVELOPMENT.md#structured-logging).
