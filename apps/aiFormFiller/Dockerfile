# Development Dockerfile for AI Form Filler with Hugging Face Local Models
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

# Copy application files
COPY apps/aiFormFiller /app/apps/aiFormFiller

# Install dependencies
WORKDIR /app/apps/aiFormFiller
RUN uv sync

# Copy environment file
COPY .env* /app/

# Expose port
EXPOSE 8080

# Run the FastAPI server
CMD ["uv", "run", "aiformfiller"]
