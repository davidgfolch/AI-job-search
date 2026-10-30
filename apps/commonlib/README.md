# Common Library

Shared Python library used across the AI Job Search monorepo components (`apps/backend`, `apps/scrapper`, `apps/viewer`, etc.).

## Contents

This package provides utility modules for:

- **Database**: MySQL connection with LAN auto-discovery (`connection_manager.py`, `network/mysql_discovery.py`).
- **Enrichment selection**: shared job filters (`sql/job_filter_builder.py`) reused by the backend and the enrichment workers, plus `sql/filter_config_selector.py` / `aiEnrichRepository.py`, which return pending jobs matching the stored `filter_configurations` first (first configuration drained until it yields nothing, later ones one job at a time) and then every other pending job in `created desc`.
- **Persistence**: Shared data maintenance logic (`mergeDuplicates.py`).
- **Configuration**: dotenv loading and precedence (`environmentUtil.py`).
- **Utilities**: General purpose helpers (`util.py`, `decorator/`, `stopWatch.py`).
- **System**: Power management utilities (`keep_system_awake.py`, `wake_timer.py`) to keep the system running during long scrap jobs.
- **Terminal**: Console output coloring (`terminalColor.py`).
- **Observability**: Structured logging via `structlog` (`observability.py`), runtime metrics collection (`services/metrics_collector.py`), and Prometheus text-format export (`prometheus_exporter.py` — converts the in-memory snapshot to `prometheus_client` format for the backend's `/metrics` endpoint).
- **Ollama**: Centralized server URL config and fallback chain (`ollama_config.py`) plus the shared HTTP client used by the Ollama-backed modules, split by responsibility between `ollama_client.py` (payload, dispatch with retries, reply normalization) and `ollama_probe.py` (server selection: fallback candidates, LAN discovery, liveness and inference probing; `resolve_ollama_url()` / `ping_ollama()` stay re-exported from `ollama_client`, so existing importers do not change). `get_configured_ollama_url()` is the single reader for the configured primary (`AI_ENRICH_OLLAMA_BASE_URL` → `AI_ENRICHSKILL_OLLAMA_BASE_URL` → `OLLAMA_BASE_URL`, first set wins), so anything resolving the same server — including `scripts/install.sh`, which drives the model pull — agrees with the modules on which host to use. `resolve_ollama_url()` / `ping_ollama()` ping each candidate (`GET /api/tags`, 5s) and return the first reachable one (primary first, then `host.docker.internal`, `localhost`, then the containerized service); when none of them answers, the LAN is scanned for an Ollama server on port 11434 (`network/ollama_discovery.py`), which `COMMONLIB_OLLAMA_DISCOVERY=False` disables (default: enabled) and `auto` (or `discover`) as the configured URL goes straight to. The scan covers the local subnet plus the common LAN subnets (`192.168.0.x`, `192.168.1.x`) so an Ollama server on another LAN machine is found automatically even from inside a Docker container; `COMMONLIB_OLLAMA_DISCOVERY_SUBNETS` (comma-separated CIDRs) adds any further subnets. Candidates are deduplicated by host IP, so a server already probed under another name (`host.docker.internal` versus its gateway IP) is not tried twice. Before sending a job, `query_ollama()` picks its server through `ollama_probe.healthy_urls()`, which runs a one-token `/api/generate` probe (`COMMONLIB_OLLAMA_PROBE_TIMEOUT`, default 30s) on the candidate and only yields a server that answers it — a runner that is stuck (it serves `/api/tags` but never returns from `/api/generate`) is skipped in seconds instead of blocking the whole generation timeout. The probe reuses the job's own options, because a different `num_ctx` makes Ollama reload the model once for the probe and again for the job (~20s per job on a CPU runner). A successful probe is remembered per server for `COMMONLIB_OLLAMA_PROBE_CACHE_SECONDS` (default 300), so the following jobs are dispatched straight to inference without re-connecting; a failed probe or a job timeout drops that server from the cache so the next job probes it again. `ollama.response` carries `load_duration` alongside `prompt_eval_count`/`eval_count`, so a slow job can be told apart from a slow generation. The request knobs (`get_num_predict()`, `get_num_ctx()`, `get_repeat_penalty()`) are shared by every Ollama-backed module and are not module-scoped: the first env var set in `AI_ENRICH_*` → `AI_ENRICHSKILL_*` order wins, so setting e.g. `AI_ENRICH_NUM_CTX` also applies to `aiEnrichSkill`. The same module exposes `backend_candidate_urls()` (`backend:8000` → `host.docker.internal:8000` → `localhost:8000`), the fallback chain `aiEnrich` uses to reach the backend API for watcher notifications.
- **Watcher notifications**: shared worker→backend client (`watcher_notify.py`). `notify_watcher(job_ids, base_url, ...)` POSTs enriched IDs to `/api/jobs/notify-watcher` so the backend matcher re-evaluates them; it is best-effort, returning `False` and logging `watcher.notify_failed` (unreachable) or `watcher.notify_rejected` (non-2xx) instead of raising, because the job is already persisted.

## Environment variables

`environmentUtil.py` loads configuration from two dotenv files at the repo root: `.env` (non-sensitive settings) and `.env.secrets` (credentials). Hot-reload (`checkEnvReload`, called by every `getEnv*`) and the Settings UI writers (`setEnv` / `setEnvBulk`) re-read the files with `load_dotenv(override=True)` when the mtime changes.

Values already present in the **process environment** (Docker Compose `environment:`, shell exports, systemd units) outrank the dotenv files. The module snapshots `os.environ` before the first load and re-asserts those entries (`_restoreProcessEnv`) after every override reload, so an edited `.env` can never clobber an injected key such as `COMMONLIB_DB_HOST` or `MONGO_URI`.

Resolution order, highest first:

1. Process environment (Compose `environment:`, shell exports) — restored after each reload.
2. `.env.secrets`
3. `.env`
4. Code defaults.

`getEnvAll()` (the Settings UI feed) merges `scripts/.env.secrets.example` defaults with the actual files, where `.env` wins over `.env.secrets` and both win over the example.

## MySQL connection

The connection pool is initialized once via `get_connection()` from `sql/connection_manager.py`. The host is resolved from the `COMMONLIB_DB_HOST` env var and the schema from `COMMONLIB_DB_NAME` (default `jobs`). Pointing `COMMONLIB_DB_NAME` at another schema (e.g. `jobs_multi`) is how a second checkout runs against the same MySQL server without touching the live `jobs` database.

When the pool is temporarily exhausted, `get_connection()` retries `COMMONLIB_DB_POOL_RETRIES` times (default 3) with backoff, treating both the internal `queue.Empty` and mysql-connector's `mysql.connector.errors.PoolError` as temporary exhaustion.

Workers call `wait_for_db()` (`sql/db_wait.py`) at startup instead of exiting when MySQL is not up yet: compose only gates the start it orchestrates, so a resumed stack would otherwise turn a missing database into a restart storm. It waits forever by default (`COMMONLIB_DB_WAIT_TIMEOUT=0`), logging `db.waiting` every `COMMONLIB_DB_WAIT_LOG_SECONDS`.

### Supported host formats

| Format | Example | Description |
|--------|---------|-------------|
| Single IP | `192.168.0.10` | Specific host |
| CIDR range | `192.168.1.0/24` | All hosts in subnet |
| IP range | `192.168.0.10-192.168.0.250` | Contiguous range |
| Abbreviated range | `192.168.0.10/99` or `192.168.0.10-99` | End octet only (same /24) |
| Comma-separated | `192.168.0.10/99,192.168.0.100/250` | Priority-ordered ranges |
| `auto` / `discover` | `COMMONLIB_DB_HOST=auto` | Skip configured hosts, scan the LAN first |

### Resolution order

1. **Configured host(s)** — `COMMONLIB_DB_HOST` values first, in order.
2. **Container chain** — `mysql_db` (compose service), `host.docker.internal` (MySQL on the Docker host), `127.0.0.1` (native run), so the same `.env` works inside a container and on the host.
3. **Direct probe** — small target lists (≤10) are tried sequentially via MySQL handshake.
4. **Concurrent scan** — ranges larger than 10 IPs are port-scanned on port 3306 (100 workers, 0.5s timeout per host), then verified in original priority order.
5. **LAN fallback** — `network/mysql_discovery.py` detects the machine's local subnet(s) and scans them for any MySQL server with the `jobs` database.

All attempts are logged at INFO/WARNING level. The resolved host is cached for the process lifetime.

## Service discovery (MySQL / MongoDB / Ollama)

All three use the same primitives (`network/discovery.py`: local IP/subnet detection, port scan, host budget) and the same shared cache (`network/discovery_cache.py`), so a stack of containers starting together performs **one** LAN scan instead of one per container and per retry:

- `COMMONLIB_DISCOVERY_CACHE` — cache file path (default `<repo>/data/discovery/cache.json`; compose mounts `./data/discovery` into every service).
- `COMMONLIB_DISCOVERY_CACHE_SECONDS` / `COMMONLIB_DISCOVERY_NEGATIVE_CACHE_SECONDS` — TTL for a found host (default 3600s) and for "nothing found" (default 60s).
- `COMMONLIB_DISCOVERY_SUBNETS` — extra CIDRs to scan, comma-separated.
- `COMMONLIB_DISCOVERY_MAX_HOSTS` — cap hosts per scan (default 0 = no cap).
- `COMMONLIB_DISCOVERY_LOCK_SECONDS` / `COMMONLIB_DISCOVERY_LOCK_STALE_SECONDS` — cross-process scan lock timeout and stale takeover.

Ollama's chain and knobs are documented under **Ollama** above; MongoDB resolves `MONGO_URI` the same way (`mongo_db` → `host.docker.internal` → `127.0.0.1`, then LAN on 27017, `auto` to scan first) in `commonlib/mongo_config.py`.

The worker healthchecks (`scripts/healthcheck/ollama_healthcheck.py`) read the cached Ollama host first, so a container that reached a LAN server through discovery is reported healthy instead of being judged against the static fallback URLs only (the healthcheck never starts a scan).

## Job enrichment selection

`aiEnrichRepository.AiEnrichRepository` selects the jobs an enrichment worker processes. `iter_pending_enrichment_batches()` yields job-id chunks drained in order:

1. Pending jobs matching the stored **watched** `filter_configurations` (`sql/filter_config_selector.py`), processing the configurations in their stored order (`WHERE watched = 1 ORDER BY ordering ASC`) and each config's own `order` (falling back to `created desc` when it is null or invalid), deduplicated across configurations. The first configuration is drained until it yields nothing; every later one is drained one job at a time, re-checking the earlier configurations for newly arrived jobs. After a chunk is enriched the jobs stop satisfying the base pending condition, so the next query returns the following chunk.
2. Every remaining pending job in `created desc`, in chunks of 10.

The first watched configuration is drained without a limit (all of its remaining matches are yielded at once); every later watched configuration is drained one job at a time.

The pending-queue fallback is drained in chunks of 10.

The `ai_enriched` condition is always stripped from a configuration (`job_filter_builder.strip_ai_enriched`), because the enrichment worker is the component that sets that flag. Every candidate must still satisfy the base pending condition: not enriched, no `ai_enrich_error`, and not ignored/discarded/closed. Null-valued filter fields (e.g. `"easy_apply": null`) are ignored instead of becoming SQL conditions. When no watched configurations exist (or they cannot be read) the selection falls back to the plain pending query. `sql/job_filter_builder.py` is the single source of truth for the filter → SQL conditions and job ordering, shared with the backend `repositories/queries/jobs_query_builder.py`.

Before querying, the selector logs `enrich.selection_source` with `source="filter_configs"` and the consulted configurations in order (`configs=[{position, id, name}, ...]`), or `source="default"` when there are no watched configurations (`reason="no_filter_configurations"`) or none matched (`reason="no_filter_config_matches"`). Every watched configuration is then logged in order via `enrich.config_working` with `position`, `config_id`, `config_name` and its `matched` count (including zero). The winning configuration for each prioritised job is kept (`FilterConfigSelector.config_for`), and `AiEnrichRepository.get_job_to_enrich` logs `job.filter_config` (`job_id`, `config` or `"NONE"`) when a worker pulls a job to enrich.

## Structured logging

`observability.py` is the shared implementation behind every app's telemetry. The event/level/console conventions, `LOG_*` variables, `job_log_context`, `footer()`, `logIdleWait()` and the output layout are documented once in [Structured Logging](../../READMEs/README_DEVELOPMENT.md#structured-logging); this section covers the library internals.

```python
from commonlib.observability import get_logger

logger = get_logger("commonlib.cv_loader")
logger.warning("cv.file_not_found", location=self.cv_location)
```

- `module` is stamped from the caller by `stamp_caller_module`, so a shared helper's record still names the app module. No call site may pass `module=` (the architecture test rejects it); data read from the stamped value uses `source_module`.
- `job_log_context(id)` binds `job_id` for every record emitted inside the block, including shared helpers; an explicit `job_id=` wins.
- `metrics_collector` (`services/metrics_collector.py`) keeps a per-module snapshot (`jobs_processed`, `jobs_failed`, `backend_unreachable`, …) persisted to `AI_ENRICH_METRICS_FILE` every 60 s; `prometheus_exporter.py` renders it for the backend's `/metrics` endpoint. See [Metrics](../../READMEs/README_METRICS.md).
- A failed `log_writer.append_jsonl` write is never fatal and never silent: the record is dropped and reported once per path as `logs.write_failed` with a `chown` hint. `metrics_collector.persist()` mirrors this with `metrics.persist_failed`.
- `print()` stays only for presentational output: in-place terminal progress (`terminalUtil.py`, `decorator/retry.py`) and the `sync/mysql_sync.py` dry-run summary. `PRINT_ALLOWLIST` in the architecture test enforces this.
- `environmentUtil.py` cannot import `observability` at module scope (circular import), so it resolves its logger lazily and logs `env.loaded` / `env.reloaded` with dotenv paths only, never values.

`console_render.py` implements `CONSOLE_RECORD` and `CONSOLE_MESSAGE`, `split_console_text()` (moves `console=` to `message`, `end=` to a private key) and ANSI stripping; the public helpers are re-exported from `observability.py`. `terminalColor.py` still provides console colors; `printHR()` is a rule-drawing primitive and is not logged.

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

## Text and JSON helpers

- `stringUtil.removeBlanks(text)` strips **every** run of newlines and backspaces
  from a text. The regex flags are passed as a keyword argument
  (`re.sub(r'[\n\b]+', '', text, flags=re.M)`): `re.sub` takes `count` before
  `flags`, so passing `re.M` positionally silently capped the replacements at 8
  and left the remaining blank runs in the returned string.
- `json_helpers.rawToJson(raw)` parses LLM-produced JSON. Its unescape step
  (`re.sub(r'\\([&.*-+#])', r'\1', res, flags=re.I | re.M)`) unescapes **every**
  escaped `&`, `.`, `*`, `-`, `+` or `#`. The same positional-argument mistake
  used to stop the step after 10 replacements, which left the backslashes in
  place and made the whole parse fail with a `json.JSONDecodeError`.

## Testing

Run the module suite through the centralized runner:

```bash
./scripts/test.sh commonlib   # Linux/Mac
.\scripts\test.bat commonlib  # Windows
```
