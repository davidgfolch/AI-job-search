# Development Dockerfile for AI Enrichment with CrewAI
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
COPY packages/commonlib /app/packages/commonlib
WORKDIR /app/packages/commonlib
RUN pip install -e .

# Copy application files
COPY apps/aiEnrich /app/apps/aiEnrich

# Install dependencies
WORKDIR /app/apps/aiEnrich
RUN uv sync

# Copy environment file
COPY .env* /app/

# Note: AI Enrichment typically runs as a scheduled/batch job
# It processes jobs not yet ai_enriched from the database
CMD ["uv", "run", "aienrich"]
