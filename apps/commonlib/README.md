# Common Library

Shared Python library used across the AI Job Search monorepo components (`apps/backend`, `apps/scrapper`, the AI workers, etc.).

## Contents

This package provides utility modules for:

- **Database**: MySQL connection with LAN auto-discovery (`connection_manager.py`, `network/mysql_discovery.py`).
- **Enrichment selection**: shared job filters and pending-job selection used by the backend and the enrichment workers (see [Job enrichment selection](#job-enrichment-selection)).
- **Persistence**: Shared data maintenance logic (`mergeDuplicates.py`).
- **Configuration**: dotenv loading and precedence (`environmentUtil.py`).
- **Utilities**: General purpose helpers (`util.py`, `decorator/`, `stopWatch.py`).
- **System**: Power management utilities (`keep_system_awake.py`, `wake_timer.py`) to keep the system running during long scrap jobs.
- **Terminal**: Console output coloring (`terminalColor.py`).
- **Observability**: Structured logging via `structlog`, runtime metrics collection, and Prometheus export for the backend's `/api/metrics` endpoint.
- **Ollama**: centralized server URL configuration and a shared HTTP client for the Ollama-backed modules. The configured URL
  (`AI_ENRICH_OLLAMA_BASE_URL`, `AI_ENRICHSKILL_OLLAMA_BASE_URL` or `OLLAMA_BASE_URL`), fallbacks, LAN discovery and probe knobs
  are documented in [Distributed execution](../../READMEs/DISTRIBUTED_EXECUTION.md#ollama-host-container-or-another-lan-machine).
- **Watcher notifications**: shared worker→backend client that POSTs enriched IDs to `/api/jobs/notify-watcher` so the backend
  matcher re-evaluates them. Delivery is best-effort: a failed notification never fails the enrichment run.

## Environment variables

`environmentUtil.py` loads configuration from two dotenv files at the repo root: `.env` (non-sensitive settings) and `.env.secrets` (credentials). The files are re-read when they change.

Values already present in the **process environment** (Docker Compose `environment:`, shell exports, systemd units) outrank the
dotenv files, so an edited `.env` can never clobber an injected key such as `COMMONLIB_DB_HOST` or `MONGO_URI`.

The Settings UI feed merges `scripts/.env.secrets.example` defaults with the actual files, where `.env` wins over `.env.secrets` and both win over the example.

## MySQL connection

The connection pool is initialized once at startup. The host is resolved from the `COMMONLIB_DB_HOST` env var and the schema
from `COMMONLIB_DB_NAME` (default `jobs`). Pointing `COMMONLIB_DB_NAME` at another schema (e.g. `jobs_multi`) is how a second
checkout runs against the same MySQL server without touching the live `jobs` database.

When the pool is temporarily exhausted, connections are retried `COMMONLIB_DB_POOL_RETRIES` times (default 3).

SELECT-only code paths use a separate pool so a burst of reads cannot exhaust the write pool. It targets the host the write
pool resolved unless `COMMONLIB_DB_READ_HOST` points somewhere else (e.g. a replica), and its size is
`COMMONLIB_DB_READ_POOL_SIZE`, defaulting to `COMMONLIB_DB_POOL_SIZE`.

Every statement is timed; one slower than `COMMONLIB_DB_SLOW_QUERY_MS` (default 200, `0` disables it) is logged. Statement parameters are never logged.

Workers wait for MySQL at startup instead of exiting when it is not up yet (`COMMONLIB_DB_WAIT_TIMEOUT=0` waits forever, `COMMONLIB_DB_WAIT_LOG_SECONDS` controls progress logging).

### Supported host formats

| Format | Example | Description |
|--------|---------|-------------|
| Single IP | `192.168.0.10` | Specific host |
| CIDR range | `192.168.1.0/24` | All hosts in subnet |
| IP range | `192.168.0.10-192.168.0.250` | Contiguous range |
| Abbreviated range | `192.168.0.10/99` or `192.168.0.10-99` | End octet only (same /24) |
| Comma-separated | `192.168.0.10/99,192.168.0.100/250` | Priority-ordered ranges |
| `auto` / `discover` | `COMMONLIB_DB_HOST=auto` | Skip configured hosts, scan the LAN first |

## Service discovery (MySQL / MongoDB / Ollama)

MySQL, MongoDB and Ollama share a discovery cache, so containers starting together perform a single LAN scan:

- `COMMONLIB_DISCOVERY_CACHE` — cache file path (default `<repo>/data/discovery/cache.json`; compose mounts `./data/discovery` into every service).
- `COMMONLIB_DISCOVERY_CACHE_SECONDS` / `COMMONLIB_DISCOVERY_NEGATIVE_CACHE_SECONDS` — TTL for a found host (default 3600s) and for "nothing found" (default 60s).
- `COMMONLIB_DISCOVERY_SUBNETS` — extra CIDRs to scan, comma-separated.
- `COMMONLIB_DISCOVERY_MAX_HOSTS` — cap hosts per scan (default 0 = no cap).
- `COMMONLIB_DISCOVERY_LOCK_SECONDS` / `COMMONLIB_DISCOVERY_LOCK_STALE_SECONDS` — cross-process scan lock timeout and stale takeover.

MongoDB uses `MONGO_URI` and the backend uses `BACKEND_URL` / `BACKEND_PORT` / `BACKEND_DISCOVERY`; Ollama's chain and knobs are
documented in [Distributed execution](../../READMEs/DISTRIBUTED_EXECUTION.md#ollama-host-container-or-another-lan-machine).
Remote scrapper log shipping reuses the backend discovery — see [Scrapper logs on a remote backend](../../READMEs/DISTRIBUTED_EXECUTION.md#scrapper-logs-on-a-remote-backend).

## Job enrichment selection

Enrichment workers process pending jobs matching the stored watched filter configurations (the same filters used in the web UI)
before the remaining pending jobs. Jobs with a previous `ai_enrich_error` or marked ignored/discarded/closed are skipped. The
selection is shared with the backend, so every enrichment cycle uses the same filters; see [Job selection](../aiEnrich/README.md#job-selection).

## Structured logging

The shared implementation, event/level/console conventions, `LOG_*` variables and output layout are documented once in
[Structured Logging](../../READMEs/README_DEVELOPMENT.md#structured-logging); runtime metrics are in [Metrics](../../READMEs/README_METRICS.md).
The metrics snapshot file is set with `AI_ENRICH_METRICS_FILE`.

```python
from commonlib.observability import get_logger

logger = get_logger("my_module")
```

## Installation

This package is managed with **Poetry**. Install the whole workspace (commonlib first) through the centralized installer:

```bash
./scripts/install.sh    # Linux/Mac
.\scripts\install.bat   # Windows
```

## Usage

This package is designed to be installed as a local dependency in other apps.

Example `pyproject.toml` dependency:

```toml
[tool.poetry.dependencies]
commonlib = {path = "../commonlib", develop = true}
```

## Text and JSON helpers

- `stringUtil.removeBlanks(text)` strips every run of newlines and backspaces from a text.
- `json_helpers.rawToJson(raw)` parses LLM-produced JSON, removing markdown fences and extra text and unescaping common escaped punctuation.

## Testing

Run the module suite through the centralized runner:

```bash
./scripts/test.sh commonlib   # Linux/Mac
.\scripts\test.bat commonlib  # Windows
```
