# Common Library

Shared Python library used across the AI Job Search monorepo components (`apps/backend`, `apps/scrapper`, `apps/viewer`, etc.).

## Contents

This package provides utility modules for:

- **Database**: MySQL connection with LAN auto-discovery (`connection_manager.py`, `network/mysql_discovery.py`).
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
- `print()` is kept only for presentational output: in-place terminal progress (`end=`, `flush=True`, `\r`) — the `terminalUtil.py` countdown and the `decorator/retry.py` progress chain — and the `sync/mysql_sync.py` dry-run summary. In-place redraws require an interactive terminal; in containers (`consoleTimerDocker`) the static countdown line is skipped and the wait is collapsed to a single `timer.started` record (no `timer.completed`), so `docker-compose logs` shows one line per idle cycle. ANSI color codes passed into the `terminalUtil` helpers are stripped before a `message` reaches the JSONL, so records never carry escape sequences.

`environmentUtil.py` is the one module that cannot import `observability` at module scope, because `observability` imports `environmentUtil`. It resolves the logger lazily inside `_logEvent()` and emits `env.loaded` (debug, once) and `env.reloaded` (info) with the dotenv file paths only — never their values. A reentrancy guard keeps the reload from recursing through `configure_logging`.

`terminalColor.py` remains for colored console output; `printHR()` is a rule-drawing primitive and is not structured-logged.

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
