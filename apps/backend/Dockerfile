# Development Dockerfile for FastAPI Backend
# Use Python 3.10 to match project requirements
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN pip install --no-cache-dir uv

# Copy commonlib first (needed for dependency resolution)
COPY packages/commonlib /app/packages/commonlib

# Copy dependency files
COPY apps/backend/pyproject.toml apps/backend/uv.lock* apps/backend/README.md /app/apps/backend/

# Install dependencies
WORKDIR /app/apps/backend
# Use --frozen to ensure we use the lockfile versions
RUN uv sync --frozen --no-install-project

# Copy application code
COPY apps/backend /app/apps/backend

# Install the project itself
RUN uv sync --frozen

# Expose port
EXPOSE 8000

# Run the application with hot-reload
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
