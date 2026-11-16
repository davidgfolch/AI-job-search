# aiEnrichSkill

Decoupled skill enrichment module supporting **Ollama** and **HuggingFace** backends.

Extracted from `aiEnrich` — provides AI-based enrichment of `job_skills` table (description and category generation).

## Backends

| Backend | Env Value | Requirements |
|---------|-----------|-------------|
| Ollama (default) | `ollama` | Ollama server running (default URL centralized as `OLLAMA_HOST_BASE_URL` in `commonlib`; configured URL falls back to the host server when unreachable) |
| HuggingFace | `huggingface` | Local transformers, GPU recommended |

## Usage

### Docker (recommended)

```bash
# From the repository root; add --profile ollama when Ollama is containerized
docker-compose --profile aiEnrichSkill up -d aienrichskill
```

The worker auto-discovers a MySQL host, an Ollama server (when the Ollama backend is selected) and the backend, so it runs unchanged on the host, in Docker or on another LAN machine. Workers stay in Docker: to pin a remote server set `AI_ENRICH_OLLAMA_BASE_URL=http://<ollama-ip>:11434` in `.env` (compose maps it to `AI_ENRICHSKILL_OLLAMA_BASE_URL`), or use `auto` to go straight to the LAN scan. Chains, subnets and the Ollama-side `OLLAMA_HOST`/firewall requirements: [Distributed execution & LAN service auto-discovery](../../READMEs/DISTRIBUTED_EXECUTION.md).

### Host runner

```bash
# From the repository root
./apps/aiEnrichSkill/run.sh    # Linux/Mac
.\apps\aiEnrichSkill\run.bat   # Windows
```

Dependencies are installed by the centralized installer (`./scripts/install.sh` / `.\scripts\install.bat`); see [Setup Guide](../../READMEs/README_INSTALL.md).

## Configuration

Set these in your `.env` or `.env.secrets`:

### General
- `AI_ENRICHSKILL_ENABLED` — Enable/disable (default: `True`)
- `AI_ENRICHSKILL_BACKEND` — Backend: `ollama` or `huggingface` (default: `ollama`)
- `AI_ENRICHSKILL_CATEGORIES` — Comma-separated skill categories (required)
- `AI_ENRICHSKILL_ENRICH_LIMIT` — Max skills per run (default: `10`)
- `AI_ENRICHSKILL_TIMEOUT` — Timeout per item in seconds (default: `90`)

### Ollama Backend
- `AI_ENRICHSKILL_OLLAMA_BASE_URL` — Ollama server URL (overrides centralized default `OLLAMA_HOST_BASE_URL` in `commonlib`). Set to `auto` to skip the fixed candidates and discover a server on the LAN
- `AI_ENRICHSKILL_OLLAMA_MODEL` — Model name (default: `ollama/qwen2.5:3b`)
- `AI_ENRICHSKILL_MAX_NEW_TOKENS` — Max output tokens (default: `2048`)
- `AI_ENRICHSKILL_NUM_CTX` — Context window sent to Ollama per request (default: auto-bucketed from prompt length, capped at `32768`)
- `AI_ENRICHSKILL_REPEAT_PENALTY` — Repetition penalty for Ollama (default: `1.0`, disabled. Ollama's `repeat_penalty` penalizes prompt tokens too, so a value above `1.0` suppresses repeating the skills named in the offer)

The three knobs above are shared with `aiEnrich` through `commonlib/ollama_config.py` and are not module-scoped: the first one set in `AI_ENRICH_*` → `AI_ENRICHSKILL_*` order wins, so an `AI_ENRICH_NUM_CTX` in `.env` also applies here.

Pull the default model before running — the HuggingFace fallback for ISPs that block the Ollama registry is documented once in [Setup Guide — Ollama & required models](../../READMEs/README_INSTALL.md#6-install-ollama--required-models).

### HuggingFace Backend
- `AI_ENRICHSKILL_HF_MODEL_ID` — Model ID (default: `Qwen/Qwen2.5-1.5B-Instruct`)
- `AI_ENRICHSKILL_HF_TEMPERATURE` — Temperature (default: `0.1`)
- `AI_ENRICHSKILL_HF_TOP_P` — Top-p (default: `0.9`)
- `AI_ENRICHSKILL_HF_REPETITION_PENALTY` — Repetition penalty (default: `1.1`)
- `AI_ENRICHSKILL_BATCH_SIZE` — Batch size for HF (default: `10`)
- `AI_ENRICHSKILL_GPU_CLEANUP` — Clear GPU cache after batch (default: `True`)
- `AI_ENRICHSKILL_INPUT_MAX_LEN` — Max input length (default: `12000`)

## Architecture

```
main.py → enrich_skills() loop
  └─ services/enrichment_service.py
       ├─ backend == "ollama"      → commonlib.ollama_client (resolve once, reuse) + commonlib.process_skill_enrichment
       └─ backend == "huggingface" → llm_client.py + llm_utils.py batch processing
```

Each idle cycle is one line: the enrichment service logs `jobs.skipped` (`message='No skills pending.'`, `reason=no_pending_skills`, `limit`) when nothing is pending, and the main loop then waits with `ai_helpers.idleWait()` — in containers the wait itself is silent, on a `WakeableTimer` that a shutdown signal cuts short, so `docker-compose logs` shows that single record per cycle; on interactive terminals `idleWait` keeps the in-place countdown. When Ollama is unreachable, `ollama.unreachable` is logged and the retry countdown runs on both paths (up to `AI_ENRICHSKILL_MAX_OLLAMA_FAILURES`, then exit).

## Dependencies

- `commonlib` (shared library)
- `requests` (Ollama HTTP client)
- `transformers`, `torch`, `accelerate` (HuggingFace backend)
