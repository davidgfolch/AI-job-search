FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY apps/commonlib /app/apps/commonlib
WORKDIR /app/apps/commonlib
RUN pip install -e .

# Copy dependency manifests only, so the dependency install stays cached until
# pyproject.toml/uv.lock change (the application source is copied after it).
WORKDIR /app/apps/aiEnrichSkill
COPY apps/aiEnrichSkill/pyproject.toml apps/aiEnrichSkill/uv.lock* apps/aiEnrichSkill/README.md ./
RUN uv sync --no-install-project

COPY apps/aiEnrichSkill /app/apps/aiEnrichSkill
RUN uv sync

# Copy healthcheck script
COPY scripts/healthcheck/ollama_healthcheck.py /app/healthcheck.py

CMD ["uv", "run", "aienrichskill"]
