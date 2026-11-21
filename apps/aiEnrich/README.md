# AI Job Enrichment

Job data enrichment service using Ollama LLMs (local) or OpenRouter (cloud).

## Overview

This application enriches job data (e.g., extracting salary, technologies); a job may have several modalities at once (REMOTE/HYBRID/ON_SITE) and the LLM extracts the full set (overwriting the deterministic scrape-time value when valid, otherwise the scrape-time value is kept). Two LLM providers are supported, selected with the `AI_ENRICH_LLM_BACKEND` environment variable:

- **Ollama** (`ollama`, default): local models, free, no API key required. Communicates over Ollama's `/api/generate` HTTP API.
- **OpenRouter** (`openrouter`): cloud models via the OpenAI-compatible API at openrouter.ai. Requires an API key, no local model/server needed.

## Job selection

Pending jobs matching the stored **watched filter configurations** (the same filters used in the web UI) are enriched before the
rest. Jobs with a previous `ai_enrich_error` or marked ignored/discarded/closed are skipped; when no watched configurations
exist, all pending jobs are processed. Selection is shared through `commonlib`, so every cycle uses the same filters.

## Installation

`aiEnrich` uses `uv` for dependency management. Install the whole workspace (including the host tools and the default Ollama model pull) through the centralized installer:

```bash
./scripts/install.sh    # Linux/Mac
.\scripts\install.bat   # Windows
```

Host prerequisites (Python, uv, npm, Docker) and `.env` setup: [Setup Guide](../../READMEs/README_INSTALL.md).

## Running

### Docker (recommended)

```bash
# From the repository root; the ollama profile is only needed when Ollama is containerized
docker-compose --profile aienrich up -d aienrich
```

The worker auto-discovers a MySQL host, an Ollama server and the backend, so the same command works with Ollama on the host, in
a container or on another LAN machine. Workers stay in Docker: to pin a remote server set
`AI_ENRICH_OLLAMA_BASE_URL=http://<ollama-ip>:11434` in `.env`, or use `auto` to go straight to the LAN scan. Chains, subnets
and the Ollama-side `OLLAMA_HOST`/firewall requirements: [Distributed execution & LAN service auto-discovery](../../READMEs/DISTRIBUTED_EXECUTION.md).

### Automated Loop (host)

```bash
# From the repository root
./apps/aiEnrich/run.sh    # Linux/Mac
.\apps\aiEnrich\run.bat   # Windows
```

## Structured logging

Records go to stdout and are mirrored to `data/logs/aiEnrich.jsonl`, which the backend dashboard and the Prometheus exporter read. The shared event/level/`LOG_*` rules are documented in [Structured Logging](../../READMEs/README_DEVELOPMENT.md#structured-logging); app-specific behaviour:

- **Progress**: `docker-compose logs` shows one progress line per job with `n/m` counters; the counters stay queryable in the JSONL.
- **Idle**: the worker waits instead of sleeping, keeping the countdown in interactive terminals.
- **Sleeping backend**: an unreachable Ollama server is waited for instead of exiting. Past `AI_ENRICH_MAX_OLLAMA_FAILURES`
  (default `3`) consecutive failures the worker keeps waiting rather than restart-looping.
- **Provider failures mid-job**: a job is deferred while the backend is unreachable. If the backend answers but produces no
  reply within `AI_ENRICH_TIMEOUT_JOB`, the job is marked with `ai_enrich_error` and leaves the pending queue, so one job that
  can never be enriched does not block the batch.
- **Attribution**: related records for a job share its `job_id`.

## Configuration



### LLM Backend Selection

Select the LLM provider with `AI_ENRICH_LLM_BACKEND` in your `.env` file. The default is `ollama`. This is separate from `AI_ENRICH_BACKEND_URL`, which points at the FastAPI backend.

### Watcher notification

After a job is successfully enriched, `aiEnrich` tells the backend to enqueue it for watcher matching so the watcher badge
updates in the UI, via `POST /api/jobs/notify-watcher`. The backend URL is read from `AI_ENRICH_BACKEND_URL` when set; otherwise
it is auto-discovered as described in [Distributed execution & LAN service auto-discovery](../../READMEs/DISTRIBUTED_EXECUTION.md).
Notification is best-effort: if the backend is unreachable the enrichment run continues and only a warning is logged.

```bash
# Optional override (e.g. when the backend is on another host):
AI_ENRICH_BACKEND_URL=http://backend:8000
```

#### Ollama backend (default)

The default model is `ollama/qwen2.5:3b` (optimized for CPU inference). To change the model, set the `AI_ENRICH_OLLAMA_MODEL` environment variable in your `.env` file:

```bash
AI_ENRICH_LLM_BACKEND=ollama
AI_ENRICH_OLLAMA_MODEL=ollama/phi3.5:3b
```

The Ollama server URL is centralized as `OLLAMA_HOST_BASE_URL` in `commonlib` and can be overridden with `AI_ENRICH_OLLAMA_BASE_URL` (set it to `auto` to skip the fixed candidates and go straight to the LAN scan). Server resolution, LAN/subnet behavior and the probe/caching knobs are documented once in [Distributed execution & LAN service auto-discovery](../../READMEs/DISTRIBUTED_EXECUTION.md#ollama-host-container-or-another-lan-machine).

> or change it in http://localhost:5173/settings (docker with web/backend must be running, see [DOCKER_DEV.md](../../READMEs/DOCKER_DEV.md))

**Recommended models for CPU-only inference:**

| Model | Speed | Accuracy |
|-------|-------|----------|
| `ollama/qwen2.5:3b` | Fast | Good |
| `ollama/phi3.5:3b` | Very Fast | Moderate |
| `ollama/llama3.2:1b` | Fastest | Lower |

Make sure the model is pulled in Ollama: [Setup Guide — Ollama & required models](../../READMEs/README_INSTALL.md#6-install-ollama--required-models), including the HuggingFace fallback for ISPs that block the Ollama registry.

#### OpenRouter backend (cloud)

Use cloud models without running a local Ollama server. No Ollama installation or model pulling is required.

Set in `.env`:

```bash
AI_ENRICH_LLM_BACKEND=openrouter
AI_ENRICH_OPENROUTER_BASE_URL=https://openrouter.ai/api/v1   # optional, has default
AI_ENRICH_OPENROUTER_MODEL=openrouter/free                    # optional, has default
AI_ENRICH_OPENROUTER_FALLBACK_MODEL=nex-agi/nex-n2.5-pro:free # optional, has default
```

And in `.env.secrets`:

```bash
AI_ENRICH_OPENROUTER_API_KEY=sk-or-...
```

Get an API key at [openrouter.ai](https://openrouter.ai/keys).

**Default model: `openrouter/free`**. It's a router that automatically picks any free model supporting structured output (zero cost). Trade-offs: rate-limited to roughly 20 requests/min and 200 requests/day, and the underlying model can change at any time. For personal/self-hosted enrichment volumes with a few dozen jobs per day this is usually fine; if you hit the limits (HTTP 429) switch to a specific cheap paid model for much higher rate limits, e.g.:

```bash
AI_ENRICH_OPENROUTER_MODEL=google/gemini-2.5-flash-lite   # ~$0.10/$0.40 per M tokens, high rate limits
```

**Fallback model: `nex-agi/nex-n2.5-pro:free`**. When the primary model returns invalid or non-JSON output, `aiEnrich` retries
with this free model. Override it with `AI_ENRICH_OPENROUTER_FALLBACK_MODEL` in `.env`.

Any OpenRouter slug works — `openai/gpt-4o-mini`, `anthropic/claude-3.5-sonnet`, `google/gemini-flash-1.5`, etc. The same `AI_ENRICH_MAX_NEW_TOKENS` and `AI_ENRICH_TIMEOUT_JOB` variables apply.

**Context window**: set `AI_ENRICH_NUM_CTX` (e.g. `32768`) when your Ollama model supports a bigger window; too small a context is the usual cause of truncated model output.

**Oversized inputs**: jobs whose prompt exceeds `AI_ENRICH_INPUT_MAX_LEN` characters (default `30000`) are not sent to the model;
they are marked with `ai_enrich_error='too long context'` instead. The web UI's **Force Re-enrich** clears the error to retry
such a job manually.

**Repetition penalty**: `AI_ENRICH_REPEAT_PENALTY` defaults to `1.0` (disabled); raise it only if you observe a repetition loop.
The knob is shared with `aiEnrichSkill` (see [aiEnrichSkill](../aiEnrichSkill/README.md#ollama-backend)).

**Strict extraction**: the model's reply is validated before saving; invalid replies are retried
(`AI_ENRICH_MAX_VALIDATION_RETRIES`, default `1`) and a job whose reply never validates is not enriched rather than saved
partially. Technology lists are de-duplicated, `modality` is upper-cased, and salary and `hybrid_info` values that are not
grounded in the offer text are discarded — e.g. a salary with no digits and an arrangement the offer does not state are not
stored.

**Company resolution**: offers published without a company are stored as `unspecified`. During enrichment a second request tries
to resolve the company; when it succeeds the job is updated and its duplicate check re-run with the real company. When no
company can be determined the job keeps `unspecified` and is still enriched — a failed guess never marks the job as failed.
