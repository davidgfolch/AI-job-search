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
