FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN pip install --no-cache-dir uv

# Set up the working directory inside the container
WORKDIR /app

# The aiEnrich3 app depends on commonlib, so we need to copy both into the container
# We assume the docker context is the mono-repo root `AI-job-search/`
COPY apps/commonlib /app/apps/commonlib
COPY apps/aiEnrich3 /app/apps/aiEnrich3

# Move into the aiEnrich3 dir
WORKDIR /app/apps/aiEnrich3

# Create the virtual environment and install dependencies
ENV UV_PROJECT_ENVIRONMENT="/app/venv"
ENV PATH="/app/venv/bin:$PATH"
RUN uv sync

# Optional: Pre-download the Hugging Face models during the build step
# so the container starts instantly when run
RUN uv run python -c "\
from gliner import GLiNER;\
from transformers import pipeline;\
GLiNER.from_pretrained('urchade/gliner_multi-v2.1');\
pipeline('zero-shot-classification', model='MoritzLaurer/mDeBERTa-v3-base-mnli-xnli');\
"

# Set the startup command
CMD ["uv", "run", "python", "src/aiEnrich3/main.py"]
