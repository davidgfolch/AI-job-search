FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc curl && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

# Copy commonlib first (needed for dependency resolution)
COPY apps/commonlib /app/apps/commonlib
WORKDIR /app/apps/commonlib
RUN pip install -e .

# Copy dependency manifests only, so the dependency install stays cached until
# pyproject.toml/uv.lock change (the app source is copied after it).
WORKDIR /app/apps/cron
# Keep the venv outside the bind-mounted app source. Otherwise Docker populates a
# fresh anonymous volume with the whole venv on every container recreate.
ENV UV_PROJECT_ENVIRONMENT="/app/venv"
ENV PATH="/app/venv/bin:$PATH"
COPY apps/cron/pyproject.toml apps/cron/uv.lock* apps/cron/README.md ./
RUN uv sync --no-install-project

# Copy application code last
COPY apps/cron /app/apps/cron
RUN uv sync

CMD ["uv", "run", "cron"]
