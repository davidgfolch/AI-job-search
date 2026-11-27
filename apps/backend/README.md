# AI Job Search API

FastAPI-based backend for the AI Job Search application. It serves the data to the frontend (`apps/web`) and interacts with the MySQL database.

## Features

- **Job API**: Endpoints to list, filter, update, and manage job offers.
- **Settings API**: Read and write `.env` / `.env.secrets` variables and scrapper state from the UI.
- **RESTful Design**: Standard HTTP methods and status codes.
- **Integration**: Works with `apps/commonlib` for database access.

## Tech Stack

- **Framework**: FastAPI
- **Server**: Uvicorn
- **Package Manager**: uv
- **Database**: MySQL (via `commonlib`)

## Setup & Running

### Installation

From the repository root:

```bash
./scripts/install.sh    # Linux/Mac
.\scripts\install.bat   # Windows
```

### Running Development Server

From the repository root:

```bash
./apps/backend/run.sh    # Linux/Mac
.\apps\backend\run.bat   # Windows
```

The API will be available at `http://localhost:8000`.

### API Documentation

Once running, you can access the interactive API docs at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Cross-Origin Requests (CORS)

The backend allows cross-origin requests from any origin without credentials, so the frontend (served on a different port,
e.g. Vite's `5173`) can reach the API and the SSE stream at `GET /api/jobs/watcher-events` cross-origin.

## Testing

Run the module suite through the centralized runner (add `commonlib` when the change involves it):

```bash
./scripts/test.sh commonlib backend   # Linux/Mac
.\scripts\test.bat commonlib backend  # Windows
```

## Structure

- `api/main.py`: Application entry point and route definitions.
- `api/settings.py`: Settings API routes.
- `models/settings.py`: Pydantic models for settings request/response.
- `services/settings_service.py`: Business logic for reading/writing `.env` / `.env.secrets` and scrapper state (MySQL).
- `repositories/`: Data access layer.

## Structured Logging

The backend emits structured JSON logs. The shared format, levels and `LOG_*` environment variables are documented in [Structured Logging](../../READMEs/README_DEVELOPMENT.md#structured-logging).

## Company Synonyms

Some companies post the same job offer under different names across platforms (e.g. *"Tech Recruiters SL"* and *"TRSL Global"*). The Company Synonyms feature links those names together so they are treated as the same entity.

### Database

Synonym groups are stored in MySQL; the table definition lives in [`scripts/mysql/ddl.sql`](../../scripts/mysql/ddl.sql).

### API Endpoints

Synonym groups can be listed, created, extended and removed through the API in [`api/company_synonyms.py`](api/company_synonyms.py).

### Job Detail Response

Job responses include company synonyms, work arrangements and extracted hybrid detail; see [`api/jobs.py`](api/jobs.py).

## Metrics API

Prometheus text-format metrics are exposed for the Prometheus service (`:9090`) and Grafana dashboard (`:3000`, admin/admin); see [`api/metrics.py`](api/metrics.py).

## Settings API

The settings API reads and writes `.env` / `.env.secrets` variables and scrapper state from the UI; see [`api/settings.py`](api/settings.py).

## Dashboard API

The dashboard reports AI module status and infrastructure health, including Ollama, Prometheus and Grafana; see [`api/dashboard.py`](api/dashboard.py).

Configuration:

- Ollama: `AI_ENRICH_OLLAMA_BASE_URL` pins the server; `COMMONLIB_DISCOVERY_SUBNETS` (comma-separated CIDRs, e.g. `10.0.0.0/24`)
  covers non-standard LAN subnets (`COMMONLIB_OLLAMA_DISCOVERY_SUBNETS` is the legacy Ollama-only alias). Discovery is documented in
  [Distributed execution](../../READMEs/DISTRIBUTED_EXECUTION.md#ollama-host-container-or-another-lan-machine).
- AI backend: `AI_ENRICH_LLM_BACKEND` selects the provider (`"ollama"` or `"openrouter"`, default `"ollama"`).
- Activity freshness: `DASHBOARD_ACTIVITY_WINDOW_SECONDS` (default `86400`).
- URL overrides: `DASHBOARD_BACKEND_URL`, `DASHBOARD_WEB_URL`, `DASHBOARD_FORM_FILLER_URL`, `PROMETHEUS_URL`, `GRAFANA_URL`; MongoDB uses `MONGO_URI`. Database URLs never expose credentials.

## Watcher API

The watcher badge shows how many jobs match each watched filter configuration since the last check, updated near-realtime via Server-Sent Events.
Endpoint details live in [`api/watcher.py`](api/watcher.py) and [`api/jobs.py`](api/jobs.py).

## Statistics API

Statistics are available for job history, sources and per-keyword scrapper totals read from scrapper JSONL logs; see [`api/statistics.py`](api/statistics.py),
[`api/keyword_stats.py`](api/keyword_stats.py) and [`api/scrapper_logs.py`](api/scrapper_logs.py).

Keyword results may be incomplete when log rotation has dropped older dates. Statistics read `SCRAPPER_LOG_DIR` (mounted read-write as `/logs/scrapper` in Docker) and make no database writes.
A scrapper on another machine can ship its records to the backend; see [Distributed execution](../../READMEs/DISTRIBUTED_EXECUTION.md#scrapper-logs-on-a-remote-backend).
