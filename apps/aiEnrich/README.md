# AI Job Enrichment

Job data enrichment service using Ollama LLMs (local) or OpenRouter (cloud).

## Overview

This application enriches job data (e.g., extracting salary, technologies, modality) using an LLM. Two backends are supported, selected with the `AI_ENRICH_BACKEND` environment variable:

- **Ollama** (`ollama`, default): local models, free, no API key required. Communicates over Ollama's `/api/generate` HTTP API.
- **OpenRouter** (`openrouter`): cloud models via the OpenAI-compatible API at openrouter.ai. Requires an API key, no local model/server needed.

## Installation

### 1. Install `uv` Package Manager

AiEnrich uses `uv` for dependency management.

```bash
# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

After installation, update shell:

```bash
uv tool update-shell
```

### 2. Install Project Dependencies

```bash
cd apps/aiEnrich
uv sync
```

## Running

### Automated Loop

To run the enrichment in a continuous loop (monitoring the database for new jobs):

```bash
# Linux
./run.sh

# Windows
.\run.bat
```

### Manual Run (Dev)

```bash
uv run aienrich
```

## Configuration

- **CV Matching**: Enable by setting `AI_ENRICH_CV_MATCH=True` in `.env` and placing your CV in `apps/aiEnrich/cv/cv.txt`.

### LLM Backend Selection

Select the backend with `AI_ENRICH_BACKEND` in your `.env` file. The default is `ollama`.

#### Ollama backend (default)

The default model is `ollama/qwen2.5:3b` (optimized for CPU inference). To change the model, set the `AI_ENRICH_OLLAMA_MODEL` environment variable in your `.env` file:

```bash
AI_ENRICH_BACKEND=ollama
AI_ENRICH_OLLAMA_MODEL=ollama/phi3.5:3b
```

The Ollama server URL is centralized as `OLLAMA_HOST_BASE_URL` in `commonlib` and can be overridden with `AI_ENRICH_OLLAMA_BASE_URL`. The module resolves the first reachable server once per cycle (configured URL first, then `host.docker.internal`, `localhost`, and the containerized `ollama:11434`) and reuses it for the whole batch — so a missing containerized Ollama transparently falls back to a host server instead of failing.

> or change it in http://localhost:5173/settings (docker with web/backend must be running, see [DOCKER_DEV.md](../READMEs/DOCKER_DEV.md))

**Recommended models for CPU-only inference:**

| Model | Speed | Accuracy |
|-------|-------|----------|
| `ollama/qwen2.5:3b` | Fast | Good |
| `ollama/phi3.5:3b` | Very Fast | Moderate |
| `ollama/llama3.2:1b` | Fastest | Lower |

Make sure the model is pulled in Ollama:

Non-dockerized (local Ollama server):
```bash
ollama pull qwen2.5:3b
```

Dockerized (Ollama container, models persisted via the mounted `~/.ollama` volume):
```bash
docker exec ai-job-search-ollama ollama pull qwen2.5:3b
```

> **ISP blocking the Ollama registry (e.g. Movistar)**: if `ollama pull` hangs with `dial tcp ...:443: i/o timeout`, the download host `r2.cloudflarestorage.com` is blocked. Pull the same model from HuggingFace and alias it instead:
> ```bash
> ollama pull hf.co/Qwen/Qwen2.5-3B-Instruct-GGUF:q4_k_m
> ollama cp hf.co/Qwen/Qwen2.5-3B-Instruct-GGUF:q4_k_m qwen2.5:3b
> ollama rm hf.co/Qwen/Qwen2.5-3B-Instruct-GGUF:q4_k_m   # temp tag shares the same files, remove to keep the list clean
> ```
> For the Dockerized server, prefix each command with `docker exec ai-job-search-ollama ollama`.

#### OpenRouter backend (cloud)

Use cloud models without running a local Ollama server. No Ollama installation or model pulling is required.

Set in `.env`:

```bash
AI_ENRICH_BACKEND=openrouter
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

**Fallback model: `nex-agi/nex-n2.5-pro:free`**. When the primary model returns invalid/non-JSON output (e.g. a `:free` route refuses with plain text), `aiEnrich` retries the request with this reliable free model in JSON mode (`response_format: {"type": "json_object"}`). Override it with `AI_ENRICH_OPENROUTER_FALLBACK_MODEL` in `.env`.

Any OpenRouter slug works — `openai/gpt-4o-mini`, `anthropic/claude-3.5-sonnet`, `google/gemini-flash-1.5`, etc. The same `AI_ENRICH_MAX_NEW_TOKENS` and `AI_ENRICH_TIMEOUT_JOB` variables apply. Both the extraction prompt and JSON output format are identical to the Ollama backend.

**Note on JSON output**: The Ollama backend enables native JSON mode (`format: json` in the prompt); OpenRouter does not send `response_format: json_object` to the primary model by default (`json_mode` defaults to `False`) because several free-model routes reject it — the fallback model does use it. The returned content is parsed by the same `rawToJson` parser in `commonlib` (which strips markdown fences, extra text, and fixes common quirks) in both backends.
