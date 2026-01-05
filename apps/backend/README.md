# AI Job Search API

FastAPI-based backend for the AI Job Search application. It serves the data to the frontend (`apps/web`) and interacts with the MySQL database.

## Features

- **Job API**: Endpoints to list, filter, update, and manage job offers.
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

- `main.py`: Application entry point and route definitions.
- `routers/`: API route handlers (if applicable).
- `models/`: Pydantic models for request/response validation.
