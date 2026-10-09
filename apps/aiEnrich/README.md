# AI Job Enrichment

Job data enrichment service using Ollama LLMs (local) or OpenRouter (cloud).

## Overview

This application enriches job data (e.g., extracting salary, technologies, modality) using an LLM. Two backends are supported, selected with the `AI_ENRICH_BACKEND` environment variable:

- **Ollama** (`ollama`, default): local models, free, no API key required. Communicates over Ollama's `/api/generate` HTTP API.
- **OpenRouter** (`openrouter`): cloud models via the OpenAI-compatible API at openrouter.ai. Requires an API key, no local model/server needed.

## Job selection

Each cycle enriches pending jobs in this priority order: first the pending jobs matching the stored **pinned filter configurations** (the same filters used by the web UI), processing the configurations in `ordering ASC` and honoring each configuration's `order` (falling back to `created desc`), then every other pending job in `created desc`. The `ai_enriched` condition is always removed from a configuration, because this module is what sets that flag, and every candidate must still be unenriched and free of a previous `ai_enrich_error` (and not ignored/discarded/closed). When no pinned configurations exist, the module falls back to the plain pending query. The selection lives in the shared `commonlib.aiEnrichRepository`, so `aiEnrichNew` and `aiEnrich3` follow the same order. The selector logs the pinned configurations in order (`enrich.selection_source`, `enrich.config_working`) and each job is logged with its originating configuration (`job.filter_config`, `NONE` when it comes from the fallback queue).

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

## Logs

Structured logging via `commonlib.observability`; records go to stdout and are mirrored to `data/logs/aiEnrich.jsonl`, which the backend dashboard and the Prometheus exporter read.

**Progress**: every enriched job ends with `footer()`, which logs one `ai.batch_completed` record carrying the `n/m` counters (`processed`, `total`, `total_processed`, `job_errors`, `config`) as fields *and* the human line in `console=` ("Processed jobs this run: n/m … Config: … Time elapsed: … (Media: …/job)"). `config` is the pinned filter configuration the job came from (`NONE` for the fallback queue). `Time elapsed:` is the current job's inference total (query + validation retries + save), also stored as `job_elapsed`, while `elapsed` / `elapsed_per_job` stay the batch wall time and its average, so the media keeps meaning "how long a job takes in this run". So the batch reads as a progress line in `docker-compose logs` while the counters stay queryable in the JSONL. `job.started` counts from 1 (`index`) so it agrees with `processed`.

**Idle**: with nothing pending, or while the backend is unreachable, the pipeline calls `logIdleWait()` rather than sleeping. It renders one record — `jobs.skipped` (`reason=no_pending_jobs`) or `ai.retry_wait` (`reason=backend_unavailable`) — with the human sentence as `message=`, then waits on a `WakeableTimer` that a shutdown signal cuts short. Interactive terminals keep the in-place countdown.

**Attribution**: each job runs inside `job_log_context(id)`, so `job.started` / `job.result` and every database record in between carry the same `job_id`, and `module` is stamped from the calling module rather than from a shared helper. See [Structured Logging](../../READMEs/README_DEVELOPMENT.md#structured-logging).

## Configuration



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

**Context window**: `aiEnrich` tells Ollama exactly how much context it needs on every request via the `num_ctx` option (auto-bucketed from prompt length + `AI_ENRICH_MAX_NEW_TOKENS`, capped at `32768`). Override with `AI_ENRICH_NUM_CTX` (e.g. `32768`) when your Ollama model supports a bigger window, or the defaults spool extra KV cache. A small `num_ctx` is the usual cause of truncated model output.

**Repetition penalty**: the Ollama backend sends `repeat_penalty=1.0` by default, i.e. **disabled**. Ollama's `repeat_penalty` penalizes tokens that already appear in the prompt, so any value above `1.0` makes repeating the offer's own technologies more expensive than emitting an empty list: at `1.3` the extraction collapsed to the shortest schema-valid output (`required_technologies: []`, `optional_technologies: []`, `salary: null`) for a large share of jobs. Degenerate repetition loops are handled without it: `num_predict` bounds the reply, and a response truncated at that limit is detected through Ollama's `done_reason="length"` and retried by the strict extraction step. Override with `AI_ENRICH_REPEAT_PENALTY` only if you observe a real loop. The knob is shared with `aiEnrichSkill` and is not module-scoped (see [aiEnrichSkill](../aiEnrichSkill/README.md#ollama-backend)).

**Strict extraction**: the response is validated against `EXTRACTION_SCHEMA` in `extraction_contract.py` (all four fields required, `additionalProperties: false`, `modality` must be `REMOTE`/`HYBRID`/`ON_SITE`, markdown code fences stripped) and sent to Ollama as a native JSON schema, so the model is constrained server-side instead of relying on prompt wording alone. When validation fails (invalid JSON, missing/extra field, wrong `modality`, or output truncated at the `num_predict` limit) the request is retried once with an explicit "the previous response was invalid" instruction. Tune with `AI_ENRICH_MAX_VALIDATION_RETRIES` (default `1`, so two attempts total; `0` disables the retry). After the last attempt the job is not saved and the reason is logged as `ai.structured_retry` / the final `ai.extract_failed` error, instead of persisting a partial row. Once the response is valid, `commonlib.ai_helpers.validateResult` normalizes it before saving: technology lists are flattened and de-duplicated, `modality` is upper-cased, and a **salary without any digit is discarded** (logged as `ai.invalid_salary`), so qualitative phrases such as "salario según experiencia" are intentionally not stored. An extraction that yields no technologies at all is logged as `ai.no_technologies`.

**Company resolution**: some job boards publish offers without a company (e.g. Tecnoempleo), and the scrapper stores them with the company set to `unspecified` instead of discarding the offer. When a job is enriched and its company is still `unspecified`, a second, independent request (`companyExtractor.py`) asks the same backend for the company only, validated against `COMPANY_SCHEMA` (`{"company": "..." | null}`) and capped to 4000 characters of the job text. If a company is returned it is saved with `AiEnrichRepository.update_unspecified_company()`, which only writes while the company is still `unspecified`, and `AiEnrichRepository.refresh_duplicated_of()` then re-runs the duplicate check with the real company (deferred at scrape time, while the company was generic). When no company can be determined, or the request fails, the job keeps `unspecified` and is enriched normally: a failed guess never marks the job as failed to enrich. Events are logged as `company.resolved`, `company.unresolved`, and `company.resolution_failed`.
