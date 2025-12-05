# Development Dockerfile for FastAPI Backend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==1.8.0

# Copy commonlib first and install it
COPY packages/commonlib /app/packages/commonlib
WORKDIR /app/packages/commonlib
RUN pip install -e .

# Copy dependency files
COPY apps/backend/pyproject.toml apps/backend/poetry.lock* /app/apps/backend/

# Install dependencies
WORKDIR /app/apps/backend
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --only main

# Copy application code
COPY apps/backend /app/apps/backend

# Expose port
EXPOSE 8000

# Run the application with hot-reload
CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
