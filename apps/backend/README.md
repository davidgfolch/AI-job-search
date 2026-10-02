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

```bash
uv sync
```

### Running Development Server

```bash
uv run uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

### API Documentation

Once running, you can access the interactive API docs at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

Run unit tests with pytest:

```bash
uv run pytest
```

## Structure

- `api/main.py`: Application entry point and route definitions.
- `api/settings.py`: Settings API routes.
- `middleware/request_logging.py`: Raw ASGI middleware that emits one structured record per HTTP request.
- `models/settings.py`: Pydantic models for settings request/response.
- `services/settings_service.py`: Business logic for reading/writing `.env` / `.env.secrets` and scrapper state (MySQL via `ScrapperStateRepository`).

## Structured Logging

Every record is a JSON line with a dotted `domain.action` event name and `key=value`
fields, written to stdout and mirrored to `data/logs/backend.jsonl` (relative to the
working directory, so `apps/backend/data/logs/backend.jsonl` on the host). Event names,
field rules, levels, and the `LOG_*` environment variables are documented once in
[Structured Logging](../../READMEs/README_DEVELOPMENT.md#structured-logging) - this
section only lists what the backend emits.

`api/main.py` calls `configure_logging("backend")` before the `FastAPI` app object is
created, so startup and every later record are attributed to the `backend` app. The
standard-library `uvicorn.access` logger is disabled at the same point: the per-request
timeline exists only as the `http.request_completed` record, so `docker-compose logs` does
not show a duplicate uvicorn access line.

### Request logging middleware

`RequestLoggingMiddleware` is added after `CORSMiddleware` (therefore the outermost
user middleware) and is pure ASGI: it reads only `http.response.start` off the send
channel and never touches a body chunk, so streaming responses are forwarded untouched
and every log call is wrapped so the middleware can never raise.

| Event | Level | When |
|---|---|---|
| `http.request_completed` | `info` | Once per request that produced a response, with `method`, `path`, `status_code`, `duration_ms`. |
| `http.request_failed` | `warning` | Additionally, when the status is outside 200-399, with the same fields. |
| `http.request_failed` | `error` | An unhandled exception: the record carries `error` plus the traceback, and the exception keeps propagating to Starlette's `ServerErrorMiddleware` (so a 500 raised there produces this record and no duplicate completed record). |

Non-HTTP scopes (websockets, lifespan) are forwarded untouched and never logged.
Bodies, headers, cookies, and query strings are never recorded: `path` is the scope
path, which excludes the query string, and only ids, counts, statuses, and durations
are ever passed as fields.

```bash
# Slow or failing requests
jq -c 'select(.event == "http.request_failed")' apps/backend/data/logs/backend.jsonl
```

### Application events

| Event | Level | Emitted by |
|---|---|---|
| `app.started` | `info` | `api/main.py`, with the `api` distribution version. |
| `api.request_rejected` | `warning` | `api/filter_configurations.py`, `api/jobs_applied.py` - a `ValueError` translated into a 400/404, with `operation`, `config_id`, `status_code`, `error`. |
| `salary.calculation_failed` | `error` | `api/salary.py`. |
| `settings.updated` | `info` | `services/settings_service.py` - `key` and `count` only, never the setting value. |
| `scrapper_state.read_failed` / `scrapper_state.write_failed` | `error` | `services/settings_service.py`. |
| `skills.save_failed` | `error` | `services/skills_service.py`. |
| `skills.parse_failed` | `warning` | `repositories/skills_repository.py` - malformed `learning_path` JSON in a row. |
| `db.query_failed` | `error` | `repositories/queries/repository_utils.py` - `error` is the driver exception class name and `syntax_error` the classification, never the SQL or its bind values. |
| `db.insert_failed` | `error` | `repositories/company_synonym_repository.py`. |
| `db.view_creation_failed` | `error` | `repositories/watcher_repository.py`. |
| `filters.parse_failed` | `warning` | `repositories/filter_configurations_repository.py` - malformed `filters` JSON in a row. |
| `watcher.filters_parse_failed` | `warning` | `repositories/watcher_repository.py`. |
| `watcher.stats_failed` | `error` | `services/watcher_service.py`. |
| `synonyms.lookup_failed` / `jobs.regex_search_failed` | `warning` | `services/jobQueryService.py` - degraded search fallbacks. |
| `logs.read_failed` / `logs.line_skipped` / `logs.timestamp_unparsed` | `debug` | `repositories/dashboard_repository.py` - a missing or half-written JSONL line is expected while another app writes. |
| `ollama.probe_failed` | `debug` | `services/dashboard_service.py`. |
| `metrics.timestamp_unparsed` | `debug` | `services/dashboard_service.py`. |

The request middleware emits `http.request_completed` (and `http.request_failed` for a non-2xx/3xx status or an unhandled exception) from `middleware/request_logging.py`. Its `module` is stamped from the caller like any other record. The dashboard repository reads other apps' records, so it re-emits the source app's stamped name as **`source_module`**, and the API keeps exposing it as `module`; the two names mean different things — `module` is always "the app module that logged this line", never "the app this line was about".

### Testing log output

`conftest.py` provides an autouse `log_records` fixture that points `LOG_DIR` at a
temporary directory, so a test run never writes into `data/logs` and any test can
assert on the records it produced:

```python
def test_get_scrapper_state_returns_empty_on_error(mock_repo, log_records):
    mock_repo.get_all.side_effect = Exception("DB error")
    assert settings_service.get_scrapper_state() == {}
    assert log_records(event="scrapper_state.read_failed")[0]["error"] == "DB error"
```

## Company Synonyms

Some companies post the same job offer under different names across platforms (e.g. *"Tech Recruiters SL"* and *"TRSL Global"*). The Company Synonyms feature links those names together so they are treated as the same entity.

### Database

A `company_synonyms` table stores synonym groups. All names sharing the same `group_id` are synonyms of each other:

```sql
CREATE TABLE company_synonyms (
  id INT NOT NULL AUTO_INCREMENT,
  name VARCHAR(200) NOT NULL UNIQUE,
  group_id INT NOT NULL,
  created DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  INDEX group_id_idx (group_id)
);
```

Example: `("Tech Recruiters SL", 1)` and `("TRSL Global", 1)` → group 1 means both are the same company.

### How it affects the applied-by-company search

When viewing a job and checking for already-applied positions:

1. The backend looks up synonyms for the current job's company name
2. The SQL query is expanded with `RLIKE` patterns for **all** synonym names (OR'd together)
3. If no exact match is found, the `search_partial_company()` fallback (word-stripping fuzzy match) is applied to **each** synonym name
4. Results include applied jobs across all synonymous company names

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/company-synonyms` | List all synonym groups |
| `GET` | `/api/company-synonyms/synonyms?company=...` | Get synonyms for a company name |
| `POST` | `/api/company-synonyms/groups` | Create new group: `{names: ["A", "B"]}` |
| `POST` | `/api/company-synonyms/groups/{group_id}` | Add name to existing group: `{name: "C"}` |
| `DELETE` | `/api/company-synonyms/names/{name}` | Remove a name from its group |

### Job Detail Response

When fetching a single job (`GET /api/jobs/{id}`), the response includes a `synonyms` field with other company names in the same synonym group, or `null` if none exist.

## Metrics API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/metrics` | Prometheus text-format endpoint scraped by Prometheus (`docker-compose` service on `:9090`). Includes per-module gauges for all collector metrics. Grafana dashboard at `:3000` (admin/admin). |

## Settings API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/settings/env` | Returns all `.env` / `.env.secrets` key-value pairs as a JSON object. |
| `PUT` | `/settings/env` | Bulk-updates one or more `.env` / `.env.secrets` variables. Returns the updated state. |
| `GET` | `/settings/scrapper-state` | Returns the scrapper state from the MySQL database. |
| `PUT` | `/settings/scrapper-state` | Saves the scrapper state to the MySQL database. |
