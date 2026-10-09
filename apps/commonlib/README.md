# Common Library

Shared Python library used across the AI Job Search monorepo components (`apps/backend`, `apps/scrapper`, `apps/viewer`, etc.).

## Contents

This package provides utility modules for:

- **Database**: MySQL connection with LAN auto-discovery (`connection_manager.py`, `network/mysql_discovery.py`).
- **Enrichment selection**: shared job filters (`sql/job_filter_builder.py`) reused by the backend and the enrichment workers, plus `sql/filter_config_selector.py` / `aiEnrichRepository.py`, which return pending jobs matching the stored `filter_configurations` first (honoring each config's `order`, falling back to `created desc`) and then every other pending job in `created desc`.
- **Persistence**: Shared data maintenance logic (`mergeDuplicates.py`).
- **Utilities**: General purpose helpers (`util.py`, `decorator/`, `stopWatch.py`).
- **System**: Power management utilities (`keep_system_awake.py`, `wake_timer.py`) to keep the system running during long scrap jobs.
- **Terminal**: Console output coloring (`terminalColor.py`).
- **Observability**: Structured logging via `structlog` (`observability.py`), runtime metrics collection (`services/metrics_collector.py`), and Prometheus text-format export (`prometheus_exporter.py` — converts the in-memory snapshot to `prometheus_client` format for the backend's `/metrics` endpoint).
- **Ollama**: Centralized server URL config and fallback chain (`ollama_config.py`) plus the shared HTTP client (`ollama_client.py`) used by the Ollama-backed modules. `resolve_ollama_url()` returns the first reachable server (primary first, then `host.docker.internal`, `localhost`, and the containerized service), so a module resolves the server once and reuses it for `ping_ollama()`/`query_ollama()`. The request knobs (`get_num_predict()`, `get_num_ctx()`, `get_repeat_penalty()`) are shared by every Ollama-backed module and are not module-scoped: the first env var set in `AI_ENRICH_*` → `AI_ENRICHSKILL_*` order wins, so setting e.g. `AI_ENRICH_NUM_CTX` also applies to `aiEnrichSkill`.

## MySQL connection

The connection pool is initialized once via `get_connection()` from `sql/connection_manager.py`. The host is resolved from the `COMMONLIB_DB_HOST` env var (default `127.0.0.1`).

### Supported host formats

| Format | Example | Description |
|--------|---------|-------------|
| Single IP | `192.168.0.10` | Specific host |
| CIDR range | `192.168.1.0/24` | All hosts in subnet |
| IP range | `192.168.0.10-192.168.0.250` | Contiguous range |
| Abbreviated range | `192.168.0.10/99` or `192.168.0.10-99` | End octet only (same /24) |
| Comma-separated | `192.168.0.10/99,192.168.0.100/250` | Priority-ordered ranges |

### Resolution order

1. **Direct probe** — small target lists (≤10) are tried sequentially via MySQL handshake.
2. **Concurrent scan** — ranges larger than 10 IPs are port-scanned on port 3306 (100 workers, 0.5s timeout per host), then verified in original priority order.
3. **LAN fallback** — if no configured host responds, `network/mysql_discovery.py` detects the machine's local subnet(s) and scans them for any MySQL server with the `jobs` database.

All attempts are logged at INFO/WARNING level. The resolved host is cached for the process lifetime.

## Job enrichment selection

`aiEnrichRepository.AiEnrichRepository` selects the jobs an enrichment worker processes. `get_pending_enrichment_ids()` returns, in order:

1. Pending jobs matching the stored **pinned** `filter_configurations` (`sql/filter_config_selector.py`), processing the configurations in their stored order (`WHERE pinned = 1 ORDER BY ordering ASC`) and each config's own `order` (falling back to `created desc` when it is null or invalid), deduplicated across configurations.
2. Every remaining pending job in `created desc`.

The `ai_enriched` condition is always stripped from a configuration (`job_filter_builder.strip_ai_enriched`), because the enrichment worker is the component that sets that flag. Every candidate must still satisfy the base pending condition: not enriched, no `ai_enrich_error`, and not ignored/discarded/closed. Null-valued filter fields (e.g. `"easy_apply": null`) are ignored instead of becoming SQL conditions. When no pinned configurations exist (or they cannot be read) the selection falls back to the plain pending query. `sql/job_filter_builder.py` is the single source of truth for the filter → SQL conditions and job ordering, shared with the backend `repositories/queries/jobs_query_builder.py`.

Before querying, the selector logs `enrich.selection_source` with `source="filter_configs"` and the consulted configurations in order (`configs=[{position, id, name}, ...]`), or `source="default"` when there are no pinned configurations (`reason="no_filter_configurations"`) or none matched (`reason="no_filter_config_matches"`). Every pinned configuration is then logged in order via `enrich.config_working` with `position`, `config_id`, `config_name` and its `matched` count (including zero). The winning configuration for each prioritised job is kept (`FilterConfigSelector.config_for`), and `AiEnrichRepository.get_job_to_enrich` logs `job.filter_config` (`job_id`, `config` or `"NONE"`) when a worker pulls a job to enrich.

## Structured logging

Modules report telemetry through `observability.py` instead of `print()`. Each module binds a logger once at module level:

```python
from commonlib.observability import get_logger

logger = get_logger("commonlib.cv_loader")
logger.warning("cv.file_not_found", location=self.cv_location)
```

Conventions:

- Event names are dotted `domain.action` (`cv.loaded`, `db.dump_started`, `skill.enrich_started`), never free text.
- Dynamic values are `key=value` fields; f-strings are never passed to a log call, so records stay queryable.
- Levels: `debug` per-item detail, `info` lifecycle, `warning` recoverable problem, `error` failed operation, `exception` for tracebacks (called inside an `except` block, traceback attached automatically).
- Secrets and PII are never logged (no env values, tokens, CV text or user content), and large blobs are passed as objects rather than pre-rendered strings.
- `module` is stamped from the calling app module by `observability.stamp_caller_module`, so a record names the module that produced it even when a shared helper logged it; the `get_logger(name)` argument is only the fallback. No call site may pass `module=` (the architecture test rejects it) — data read from the stamped value uses `source_module`.
- `job_log_context(id)` binds `job_id` for the records emitted inside the block, including those from shared helpers like `sql.query_executor`, and unbinds it on exit (also on an exception). An explicit `job_id=` on a call wins over the context.
- `print()` is kept only for presentational output: in-place terminal progress (`end=`, `flush=True`, `\r`) — the `terminalUtil.py` countdown and the `decorator/retry.py` progress chain — and the `sync/mysql_sync.py` dry-run summary. In-place redraws require an interactive terminal; `ai_helpers.logIdleWait()` instead logs one rendered record — the human sentence as `message=`, with the event, `wait_seconds` and `reason` as fields — and then waits on a `WakeableTimer`, so `docker-compose logs` shows one readable line per idle cycle (`ai_helpers.idleWait()` is the same wait without a record, when the cycle's event was already logged). `ai_helpers.footer()` does the same for a batch summary (`ai.batch_completed`, with the `n/m` counters as fields). ANSI color codes passed into these helpers are stripped before a `message` reaches the JSONL, so records never carry escape sequences.

`environmentUtil.py` is the one module that cannot import `observability` at module scope, because `observability` imports `environmentUtil`. It resolves the logger lazily inside `_logEvent()` and emits `env.loaded` (debug, once) and `env.reloaded` (info) with the dotenv file paths only — never their values. A reentrancy guard keeps the reload from recursing through `configure_logging`.

`terminalColor.py` remains for colored console output; `printHR()` is a rule-drawing primitive and is not structured-logged.

### Console fields

`console_render.py` implements the two console modes an app can select with `configure_logging(app, console=...)`:

- `CONSOLE_RECORD` (default): every record is rendered on stdout as `timestamp [app] [level] event message=... fields...` — the `[app]` tag (`logger`) is bracketed right after the timestamp, `message` is the first named field, and the rest follow.
- `CONSOLE_MESSAGE`: only the text of the `console=` field is printed; records without it go to the JSONL alone. This is how a host app keeps a human console and a silent library.

`split_console_text()` moves `console=` into the record's `message` and `end=` into the private `_console_end`, so neither the raw ANSI text nor the terminator reaches the file; `log_writer.public_record()` drops the private keys. Both helpers are also what strips ANSI from a `message`. `color_enabled()`, `console_mode()`, `set_console_mode()` and `render_console()` are re-exported from `observability.py`.

## Installation

This package is managed with **Poetry**.

```bash
poetry install
```

## Usage

This package is designed to be installed as a local dependency in other apps.

Example `pyproject.toml` dependency:

```toml
[tool.poetry.dependencies]
commonlib = {path = "../commonlib", develop = true}
```

## Testing

Run tests with pytest:

```bash
poetry run pytest
```
