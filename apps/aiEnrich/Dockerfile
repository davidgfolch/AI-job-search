# Development Dockerfile for AI Enrichment with Ollama
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN pip install --no-cache-dir uv

# Copy commonlib first and install it
COPY apps/commonlib /app/apps/commonlib
WORKDIR /app/apps/commonlib
RUN pip install -e .

# Copy dependency manifests only, so the dependency install stays cached until
# pyproject.toml/uv.lock change (the application source is copied after it).
WORKDIR /app/apps/aiEnrich
COPY apps/aiEnrich/pyproject.toml apps/aiEnrich/uv.lock* apps/aiEnrich/README.md ./
RUN uv sync --no-install-project

# Copy application files
COPY apps/aiEnrich /app/apps/aiEnrich
RUN uv sync

# Copy healthcheck script
COPY scripts/healthcheck/ollama_healthcheck.py /app/healthcheck.py

# Note: AI Enrichment typically runs as a scheduled/batch job
# It processes jobs not yet ai_enriched from the database
CMD ["uv", "run", "aienrich"]
