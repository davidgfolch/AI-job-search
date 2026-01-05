# Development Dockerfile for AI Enrichment New with Hugging Face Local Models
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
# gcc and curl are standard basics
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

# Copy application files
COPY apps/aiEnrichNew /app/apps/aiEnrichNew

# Install dependencies
WORKDIR /app/apps/aiEnrichNew
RUN uv sync

# Copy environment file
COPY .env* /app/

# Note: AI Enrichment typically runs as a scheduled/batch job
CMD ["uv", "run", "aienrichnew"]
