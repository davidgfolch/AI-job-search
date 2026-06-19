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

COPY apps/aiEnrichSkill /app/apps/aiEnrichSkill

WORKDIR /app/apps/aiEnrichSkill
RUN uv sync

COPY .env* /app/

CMD ["uv", "run", "aienrichskill"]
