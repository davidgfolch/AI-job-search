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
- `models/settings.py`: Pydantic models for settings request/response.
- `services/settings_service.py`: Business logic for reading/writing `.env` / `.env.secrets` and scrapper state (MySQL via `ScrapperStateRepository`).

## Metrics API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/enrichment/metrics` | Returns per-module enrichment metrics from `commonlib`'s `MetricsCollector` (jobs, durations p50/p90/p99, errors, cache stats). See [`commonlib`](../commonlib/README.md#observability). |

## Settings API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/settings/env` | Returns all `.env` / `.env.secrets` key-value pairs as a JSON object. |
| `PUT` | `/settings/env` | Bulk-updates one or more `.env` / `.env.secrets` variables. Returns the updated state. |
| `GET` | `/settings/scrapper-state` | Returns the scrapper state from the MySQL database. |
| `PUT` | `/settings/scrapper-state` | Saves the scrapper state to the MySQL database. |
