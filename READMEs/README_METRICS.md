# AI Job Search — Metrics & Observability

## Business Overview

This project tracks performance metrics for AI-powered job enrichment operations. The enrichment pipeline extracts structured data (technologies, salary, modality) from raw job postings using three different approaches:

| Module | Technology | Speed | Use Case |
|--------|-----------|-------|----------|
| **aiEnrich** | Ollama + CrewAI (LLM) | Slow (~10s/job) | Full LLM-based extraction |
| **aiEnrich3** | GLiNER + mDeBERTa + Regex (CPU) | Fast (~0.5s/job) | CPU-optimized extraction |
| **aiEnrichNew** | HuggingFace Transformers (Qwen2.5) | Medium (~3s/job) | Batch inference, preferred |

Metrics enable answering:

- Which enrichment module is fastest for each job?
- How does enrichment time trend over days/weeks?
- What is the error rate per module?
- Are there performance regressions after model changes?

## Architecture

```
┌──────────────┐    JSONL logs     ┌──────────────────┐   /api/metrics    ┌────────────┐
│  aiEnrich     │ ────────────────► │                  │ ────────────────► │ Prometheus  │
│  aiEnrich3    │ ────────────────► │  Backend (FastAPI)│                   │ (time-series│
│  aiEnrichNew  │ ────────────────► │                  │                   │   DB)       │
└──────────────┘                   │  + MetricsCollector│                   └──────┬─────┘
                                   │  + Log parser      │                          │
                                   └──────────────────┘                     ┌──────┴─────┐
                                                                           │  Grafana    │
                                    ┌──────────────┐                       │ (dashboards)│
                                    │  Metrics JSON │                      └────────────┘
                                    │  (aggregate)  │
                                    └──────────────┘
```

### Data Flow

1. Each enrichment app records per-job **duration** and logs it as a structured JSONL event (`job.result` with `duration` field)
2. An in-process `MetricsCollector` singleton maintains a rolling window of the last 1000 durations per module and persists aggregates to `data/metrics/enrichment_metrics.json`
3. The backend FastAPI server serves `/api/metrics` which combines:
   - **Snapshot metrics** from `MetricsCollector` (aggregate p50/p90/p99/avg per module)
   - **Log metrics** by reading each app's `app.jsonl` file and extracting recent `job.result` events with durations
4. Prometheus scrapes `/api/metrics` every 15s and stores time series
5. Grafana queries Prometheus for dashboard visualization

## Metrics Pipeline

### MetricsCollector (`commonlib/services/metrics_collector.py`)

Singleton class that accumulates per-module stats:

- **Rolling window**: Last 1000 raw durations per module
- **Persisted to**: `data/metrics/enrichment_metrics.json` (shared Docker volume)
- **Computed on snapshot**: p50, p90, p99, avg from the rolling window
- **Called from**: Each enrichment app after processing each job

```python
collector.record_job("aiEnrichNew", duration_seconds, success=True)
collector.set_pending("aiEnrichNew", pending_count)
collector.record_error("aiEnrichNew", "error message")
```

### Prometheus Exporter (`commonlib/prometheus_exporter.py`)

Two functions generate Prometheus-formatted metrics:

**`build_prometheus_metrics(snapshot)`** — Aggregate metrics from MetricsCollector:
- `ai_enrich_jobs_processed_total{module}` — Total jobs attempted
- `ai_enrich_jobs_succeeded_total{module}` — Successful jobs
- `ai_enrich_jobs_failed_total{module}` — Failed jobs
- `ai_enrich_duration_seconds_total{module}` — Sum of all durations
- `ai_enrich_duration_seconds_p50/p90/p99/avg{module}` — Percentile/avg durations
- `ai_enrich_pending_jobs{module}` — Currently queued jobs
- `ai_enrich_cache_hits_total{module}`, `ai_enrich_cache_misses_total{module}`
- `ai_enrich_total_jobs` — Global total across modules
- `ai_enrich_total_errors` — Global error count
- `ai_enrich_modules_count` — Number of reporting modules

**`build_log_metrics()`** — Per-job durations from JSONL log files:
- `ai_enrich_job_duration_seconds{module, job_id}` — Individual job duration in seconds
- Sources: `/logs/aienrich/app.jsonl`, `/logs/aienrich3/app.jsonl`, `/logs/aienrichnew/app.jsonl`
- Window: Last 50 `job.result` events per module

### Log Format

Each enrichment app writes structured JSONL logs to `data/logs/app.jsonl` (container-local, bind-mounted to host). The structlog library adds ISO timestamps automatically.

Key log events:
```json
{"event": "job.started", "job_id": 123, "module": "aiEnrich", "timestamp": "..."}
{"event": "job.result", "job_id": 123, "duration": 12.5, "result": {...}, "timestamp": "..."}
{"event": "job.failed", "job_id": 123, "error": "...", "timestamp": "..."}
```

The `duration` field was added to `job.result` events across all three enrichment apps for this metrics pipeline.

### Per-Job Timing Details

| Module | Timing Source | What's Measured |
|--------|-------------|-----------------|
| aiEnrich | `time.time() - start_time` around entire job fetch+LLM+save cycle | Total wall-clock time per job |
| aiEnrich3 | `time.time() - job_start` around pipeline extraction + save | Total per-job (sequential) |
| aiEnrichNew | `time.time()` delta between consecutive `on_success` callbacks | Post-batch-inference processing time (parse + save) |

For aiEnrichNew, batch inference time is logged separately as `batch.inference_complete` with a `duration` field.

## Infrastructure

### Prometheus (`docker-compose.yml:318`)

- Image: `prom/prometheus:latest`
- Config: `docker/prometheus/prometheus.yml`
- Scrapes `backend:8000/api/metrics` every 15s
- Volume: `prometheus_data` for time series storage
- Port: `${PROMETHEUS_PORT:-9090}`

### Grafana (`docker-compose.yml:334`)

- Image: `grafana/grafana:latest`
- Datasources (provisioned): `docker/grafana/datasources/prometheus.yml`
  - Prometheus at `http://prometheus:9090`
- Dashboards (provisioned): `docker/grafana/dashboards/`
  - `enrichment_dashboard.json` — AI Enrichment Performance
- Volume: `grafana_data` for dashboard settings
- Port: `${GRAFANA_PORT:-3000}`
- Credentials: `admin` / `admin` (configurable)

### Docker Volume Mounts for Logs

Each enrichment service mounts its log directory to the host, and the backend mounts them read-only:

| Service | Host Path | Container Path |
|---------|-----------|----------------|
| aiEnrich | `./apps/aiEnrich/data/logs` | `/app/apps/aiEnrich/data/logs` |
| aiEnrich3 | `./apps/aiEnrich3/data/logs` | `/app/apps/aiEnrich3/data/logs` |
| aiEnrichNew | `./apps/aiEnrichNew/data/logs` | `/app/apps/aiEnrichNew/data/logs` |
| backend | `./apps/aiEnrich/data/logs` | `/logs/aienrich:ro` |
| backend | `./apps/aiEnrich3/data/logs` | `/logs/aienrich3:ro` |
| backend | `./apps/aiEnrichNew/data/logs` | `/logs/aienrichnew:ro` |

## Dashboard

The provisioned dashboard **AI Enrichment Performance** (`uid: ai-enrichment-performance`) includes:

| Panel | Type | Description |
|-------|------|-------------|
| Total Jobs Processed | Stat | Global job count across all modules |
| Total Errors | Stat | Global error count |
| Active Modules | Stat | Number of modules with data |
| Pending Jobs by Module | Bar gauge | Queue depth per module |
| Jobs Processed by Module | Bar gauge | Volume per module |
| Success vs Failed by Module | Bar gauge | Success/failure ratio per module |
| Duration p50 by Module | Bar gauge | Median duration per module |
| Duration Percentiles | Table | p50/p90/p99/avg per module |
| **Per-Job Duration (from logs)** | **Time series** | **Individual job durations over time with module color-coding** |

### Accessing the Dashboard

```bash
# Start the stack
docker-compose up -d

# Access Grafana
open http://localhost:3000  # admin / admin

# Access Prometheus
open http://localhost:9090
```

The dashboard auto-loads via provisioning files.

## Adding a New Enrichment Module

To add metrics for a new enrichment app (e.g., `aiEnrich4`):

1. **Log duration**: Add `duration` field to `job.result` log events in the new app
2. **MetricsCollector**: Call `collector.record_job("aiEnrich4", duration, success)` after each job
3. **Log mount**: Add the log directory mount in `docker-compose.yml` for both the new service and backend
4. **prometheus_exporter.py**: Add the new log source path to `LOG_SOURCES`
5. **Dashboard**: Add new panels or the module will auto-appear in existing `{module=~"aiEnrich.*"}` queries

## Troubleshooting

**No metrics in Prometheus/Grafana:**
- Verify backend is running: `curl http://localhost:8000/metrics`
- Check Prometheus targets UI: `http://localhost:9090/targets`
- Verify log files exist: `ls apps/aiEnrich/data/logs/app.jsonl`

**No per-job duration data:**
- Check that the enrichment app has run and processed jobs
- Verify `duration` field appears in log entries: `tail -5 apps/aiEnrich/data/logs/app.jsonl | grep job.result`
- Check log mounts in backend container: `docker exec ai-job-search-backend ls /logs/aienrich/`
