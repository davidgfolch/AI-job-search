# Plan 0: Observability (Foundation for All Improvements)

## Status: **IMPLEMENT FIRST** — before any speed improvements

## Goal

Add structured logging and runtime metrics to all `aiEnrich*` modules, with a backend API endpoint to expose them. This provides visibility into current performance (baseline) and measures the impact of subsequent speed improvements.

## Rationale

Currently every module uses raw `print()` with colored terminal output. There is no way to:
- Query how many jobs were enriched in the last hour
- Know average time per job
- Track error rates over time
- Compare performance before/after changes

Without observability, you can't measure whether speed improvements actually work. This is the prerequisite for all other plans.

## Architecture

```
aiEnrich / aiEnrichNew / aiEnrich3
  │
  ├─ structlog → console (colored, human-friendly)
  │            → file (JSON Lines, machine-parseable)
  │
  ├─ MetricsCollector (singleton, in commonlib)
  │     └─ aggregates in memory
  │         └─ persists to data/metrics/enrichment_metrics.json
  │
  └─ backend API endpoint ← reads metrics file ← GET /api/enrichment/metrics
        └─ returns JSON (ready for future Prometheus scraping)
```

## Files to Create

### `apps/commonlib/commonlib/observability.py`

Structured logging configuration:

```python
import structlog
from commonlib.environmentUtil import getEnv, getEnvBool

LOG_DIR = getEnv("AI_ENRICH_LOG_DIR", "data/logs")
LOG_FILE = f"{LOG_DIR}/aienrich.jsonl"

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer() if getEnvBool("AI_ENRICH_LOG_COLOR", True)
        else structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

def get_logger(name: str):
    return structlog.get_logger(name)
```

Simplified: one `get_logger(name)` that logs to console with colors (replacing `print()`), with a JSON file handler appended.

### `apps/commonlib/commonlib/metrics_collector.py`

```python
import json, os, time, threading
from collections import defaultdict

METRICS_FILE = getEnv("AI_ENRICH_METRICS_FILE", "data/metrics/enrichment_metrics.json")

class MetricsCollector:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._modules: dict[str, dict] = defaultdict(lambda: {
            "jobs_processed": 0, "jobs_succeeded": 0, "jobs_failed": 0,
            "total_duration": 0.0, "durations": [],
            "cache_hits": 0, "cache_misses": 0,
            "last_processed_at": None, "last_error_at": None, "last_error": None,
            "pending_jobs": 0,
        })
        self._load()

    def record_job(self, module: str, duration: float, success: bool):
        with self._lock:
            m = self._modules[module]
            m["jobs_processed"] += 1
            m["total_duration"] += duration
            m["durations"].append(duration)
            if len(m["durations"]) > 1000:
                m["durations"].pop(0)
            if success:
                m["jobs_succeeded"] += 1
            else:
                m["jobs_failed"] += 1
            m["last_processed_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")

    def record_error(self, module: str, error: str):
        with self._lock:
            m = self._modules[module]
            m["last_error_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            m["last_error"] = error[:200]

    def set_pending(self, module: str, count: int):
        with self._lock:
            self._modules[module]["pending_jobs"] = count

    def get_snapshot(self) -> dict:
        with self._lock:
            result = {}
            for name, m in self._modules.items():
                d = dict(m)
                durations = d.pop("durations")
                if durations:
                    sorted_d = sorted(durations)
                    n = len(sorted_d)
                    d["p50"] = sorted_d[n // 2]
                    d["p90"] = sorted_d[int(n * 0.9)]
                    d["p99"] = sorted_d[int(n * 0.99)]
                    d["avg"] = sum(sorted_d) / n
                result[name] = d
            return {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "modules": result,
                "global": {
                    "total_jobs": sum(m["jobs_processed"] for m in self._modules.values()),
                    "total_errors": sum(m["jobs_failed"] for m in self._modules.values()),
                }
            }

    def persist(self):
        os.makedirs(os.path.dirname(METRICS_FILE), exist_ok=True)
        with open(METRICS_FILE, "w") as f:
            json.dump(self.get_snapshot(), f, indent=2)

    def _load(self):
        if os.path.exists(METRICS_FILE):
            try:
                with open(METRICS_FILE) as f:
                    for name, mdata in json.load(f).get("modules", {}).items():
                        m = self._modules[name]
                        for k, v in mdata.items():
                            if k not in ("p50", "p90", "p99", "avg"):
                                m[k] = v
            except (json.JSONDecodeError, IOError):
                pass
```

### `apps/backend/api/metrics.py`

```python
import json, os
from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["metrics"])
METRICS_FILE = os.getenv("AI_ENRICH_METRICS_FILE", "data/metrics/enrichment_metrics.json")

@router.get("/enrichment/metrics")
def get_enrichment_metrics():
    path = os.path.abspath(METRICS_FILE)
    if not os.path.exists(path):
        return {"status": "no_data", "message": "Metrics file not found", "path": path}
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Files to Modify

### commonlib

| File | Change |
|------|--------|
| `commonlib/pyproject.toml` | Add `structlog>=24.0.0` to dependencies |

### aiEnrich (3 files)

| File | Change |
|------|--------|
| `src/aiEnrich/dataExtractor.py` | Replace print() with `logger.info/error`; wrap job processing with `collector.record_job()` |
| `src/aiEnrich/crew.py` | Add loop metrics + periodic `collector.persist()` |
| `src/aiEnrich/skillEnricher.py` | Replace print() with logger |

### aiEnrichNew

| File | Change |
|------|--------|
| `src/aiEnrichNew/dataExtractor.py` | Replace print() with logger |
| `src/aiEnrichNew/llm_utils.py` | Log batch inference duration |
| `src/aiEnrichNew/skillEnricher.py` | Replace print() with logger |

### aiEnrich3

| File | Change |
|------|--------|
| `src/aiEnrich3/dataExtractor.py` | Replace print() with logger |
| `src/aiEnrich3/pipeline.py` | Log each extraction sub-step duration |

### backend

| File | Change |
|------|--------|
| `api/main.py` | Add `from api import metrics` + `app.include_router(metrics.router, ...)` |

## Dependencies

- `structlog>=24.0.0` — single dependency in `commonlib/pyproject.toml`

## What Each Log Line Replaces

| Current (`print()`) | New (`logger.*`) |
|---|---|
| `print(green(f'AI enrich job...'))` | `logger.info("job.started", job_id=id, ...)` |
| `print(magenta(json.dumps(result)))` | `logger.info("job.result", job_id=id, salary=..., skills=...)` |
| `print(red(traceback.format_exc()))` | `logger.error("job.failed", job_id=id, error=...)` |
| `print(yellow(f'{jobIds}'))` | `logger.debug("job.pending_ids", ids=job_ids)` |
| `printHR(yellow)` | (removed — use structured separator in log) |

Keep one terminal line per job for progress feedback (e.g., `print(f"[{idx+1}/{total}] id={id} {time:.2f}s")`) — this is user-facing, not logging.

## Implementation Order

1. Create `commonlib/commonlib/observability.py`
2. Create `commonlib/commonlib/metrics_collector.py`
3. Add `structlog` to `commonlib/pyproject.toml`, run `uv sync`
4. Migrate `aiEnrich` (3 files — largest impact, start here)
5. Migrate `aiEnrichNew`
6. Migrate `aiEnrich3`
7. Create `backend/api/metrics.py`
8. Register router in `backend/api/main.py`
9. Test: run enrichment, verify JSON file at `data/metrics/enrichment_metrics.json`, verify `GET /api/enrichment/metrics` returns data

## Prometheus + Grafana (Phase 2 — Implemented)

```
Phase 1 (now):    print() → structlog + MetricsCollector → JSON file → backend API
Phase 2 (done):   commonlib/prometheus_exporter.py converts snapshot → Prometheus format
                  backend /metrics endpoint → served as text/plain via prometheus_client
                  Prometheus scrapes backend:8000/metrics
                  Grafana dashboards via provisioned datasource
                  docker-compose includes prometheus + grafana services
```

### Architecture

```
aiEnrich* apps → MetricsCollector → JSON file
                    ↓ (read by backend)
Backend /api/enrichment/metrics  (JSON, kept for backward compat)
Backend /metrics                 (Prometheus text format via prometheus_client)
                    ↓ (scraped)
Prometheus (port 9090)
    ↓ (queried)
Grafana (port 3000, admin/admin)
```

### Files

| File | Purpose |
|------|---------|
| `apps/commonlib/commonlib/prometheus_exporter.py` | Converts MetricsCollector snapshot → Prometheus format |
| `apps/backend/api/metrics.py` | Exposes `/enrichment/metrics` (JSON) and `/metrics` (Prometheus) |
| `docker/prometheus/prometheus.yml` | Prometheus scrape config |
| `docker/grafana/datasources/prometheus.yml` | Grafana Prometheus datasource |
| `docker/grafana/dashboards/enrichment_dashboard.json` | Pre-built Grafana dashboard |
| `docker/grafana/dashboards/dashboard.yml` | Dashboard provisioning config |

### Usage

```bash
docker-compose up -d prometheus grafana
# Prometheus: http://localhost:9090
# Grafana:    http://localhost:3000 (admin/admin)
# Dashboard: "AI Enrichment Performance" (auto-provisioned)
```

The data model uses `Gauge` metrics (not `Counter`/`Histogram`) because the backend reads absolute values from the shared JSON file, not live process counters. This avoids per-process scrape targets while still providing full Prometheus compatibility.
