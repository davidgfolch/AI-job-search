# Development Dockerfile for AI CV Matcher
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

# Copy dependency manifests only, so the dependency install stays cached until
# pyproject.toml/uv.lock change (the application source is copied after it).
WORKDIR /app/apps/aiCvMatcher
COPY apps/aiCvMatcher/pyproject.toml apps/aiCvMatcher/uv.lock* apps/aiCvMatcher/README.md ./
RUN uv sync --no-install-project

# Copy application files
COPY apps/aiCvMatcher /app/apps/aiCvMatcher
RUN uv sync

CMD ["uv", "run", "aicvmatcher"]
