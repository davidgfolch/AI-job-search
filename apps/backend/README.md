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
