# AI CV Matcher

This module handles fast CV matching against job descriptions using local Hugging Face embedding models (`sentence-transformers`). It acts as a dedicated microservice that continuously polls the database for pending CV matches if `AI_CVMATCHER_ENABLED` is enabled in the environment.

## Requirements

- Python >= 3.11, <3.13
- MySQL Database (Shared within monorepo)
- `uv` package manager

## Quickstart

Dependencies are installed from the repository root with `./scripts/install.sh` (Linux/Mac) or `.\scripts\install.bat` (Windows).

Configure `.env` with:
```env
AI_CVMATCHER_ENABLED=True
AI_CVMATCHER_LIMIT=100
```
Then run via Docker:
```bash
docker-compose up -d aicvmatcher
```

There is no `run.sh` runner for this module. On the host, install the dependencies as above and run it directly:

```bash
cd apps/aiCvMatcher
uv run aicvmatcher
```

## Structured logging

Telemetry goes through `commonlib.observability`; see [Structured Logging](../../READMEs/README_DEVELOPMENT.md#structured-logging) for event conventions, output layout and shared `LOG_*` variables.
The CV is never logged, and neither are job descriptions or the embedding vectors.

### Configuration

| Variable | Default | Description |
|---|---|---|
| `AI_CVMATCHER_ENABLED` | — | Runs the match loop when true; `app.disabled` and exit otherwise |
| `AI_CVMATCHER_LIMIT` | `100` | Maximum jobs pulled per batch |
