# Development Dockerfile for Streamlit Viewer
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy commonlib first and install it
COPY packages/commonlib /app/packages/commonlib
WORKDIR /app/packages/commonlib
RUN pip install -e .

# Copy viewer application code
COPY apps/viewer /app/apps/viewer

# Install viewer with dependencies
WORKDIR /app/apps/viewer
RUN pip install -e .

# Expose Streamlit port
EXPOSE 8501

# Run Streamlit with proper configuration for Docker
CMD ["streamlit", "run", "viewer/main.py", "--server.address", "0.0.0.0", "--server.port", "8501", "--server.headless", "true"]
