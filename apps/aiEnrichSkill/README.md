# aiEnrichSkill

Decoupled skill enrichment module supporting **Ollama** and **HuggingFace** backends.

Extracted from `aiEnrich` — provides AI-based enrichment of `job_skills` table (description, category and learning-path links).

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

### Learning paths

The model proposes links, and the worker validates them over outbound HTTPS before persisting: bare homepages and links unrelated to the skill are dropped, and the surviving links are ordered documentation → tutorial/course → video/social (secondary). Unreachable links degrade to a skill-scoped documentation search, plus a skill-specific video search when a video was requested; a bare domain root is never persisted. Existing user-curated links are never overwritten (updates only run when `learning_path IS NULL OR JSON_LENGTH(learning_path) = 0`).

- `AI_ENRICHSKILL_LEARNING_PATHS` — Enable the whole feature (default: `True`). `False` removes the prompt section and disables the idle backfill.
- `AI_ENRICHSKILL_LEARNING_PATH_MAX` — Links requested/persisted per skill (default: `3`)
- `AI_ENRICHSKILL_LEARNING_PATH_BATCH` — Skills per idle backfill pass (default: `1`)
- `AI_ENRICHSKILL_LEARNING_PATH_TIMEOUT` — HTTP probe timeout for link validation, in seconds (default: `5`). The links-only generation call uses `AI_ENRICHSKILL_TIMEOUT`.
- `AI_ENRICHSKILL_LEARNING_PATH_MAX_FAILURES` — Consecutive failures before the idle pass backs off for the process lifetime (default: `3`)
- `AI_ENRICHSKILL_LEARNING_DOMAINS` — Comma-separated trusted-domain allowlist override (defaults to the built-in documentation/course/video list in `config.py`)

## Architecture

```
main.py → loop
  ├─ repositories/skill_repository.py — every job_skills query (services never import MysqlUtil)
  ├─ tier 1 (interactive): enrich_skills()  → skills with ai_enriched = 0
  │    └─ services/enrichment_service.py
  │         ├─ backend == "ollama"      → commonlib.ollama_client (resolve once, reuse) + commonlib.process_skill_enrichment
  │         └─ backend == "huggingface" → services/hf_enrichment.py + llm_client.py + llm_utils.py batch processing
  └─ tier 2 (idle): enrich_learning_paths() → ai_enriched = 1 AND learning_path empty
       └─ services/learning_path_service.py (links-only prompt, validated by services/link_validator.py)
```

Tier 1 runs on user action (a new skill or *Auto-fill with AI*) and produces description, category and links in that same call. Tier 2 is the low-priority backfill for already-enriched skills. It uses the shared `data/metrics` mount as an inference slot (`commonlib/ollama_activity.py`): normal requests hold a shared lock, the backfill needs it exclusively, so it starts only while the model is free, never overlaps another request, and re-checks between items so real work preempts it. Tier 2 is Ollama-only; the HuggingFace path writes links during tier 1. The backfill writes legitimate worker output to `job_skills`, so it needs outbound HTTPS from the container.

Each idle cycle is one line: the enrichment service logs `jobs.skipped` (`message='No skills pending.'`, `reason=no_pending_skills`, `limit`) when nothing is pending, and the main loop then waits with `ai_helpers.idleWait()` — in containers the wait itself is silent, on a `WakeableTimer` that a shutdown signal cuts short, so `docker-compose logs` shows that single record per cycle; on interactive terminals `idleWait` keeps the in-place countdown. When the model is busy the loop retries every ~3 s and logs `skill.learning_path.deferred` once per busy streak (`reason=model_busy`, `model_busy_seconds`), and every backfilled skill logs `skill.learning_path.saved` (`skill`, `links`, `duration`). An unreachable Ollama is only ever waited for: `ollama.unreachable` at startup, `ai.unreachable` on an enrichment cycle, with the pending skills left pending and nothing written off (`ollama.waiting_after_failures` is logged past `AI_ENRICHSKILL_MAX_OLLAMA_FAILURES` instead of exiting). A skill Ollama answers for but cannot describe within `AI_ENRICHSKILL_TIMEOUT` is the opposite case: it is marked `ai_enriched = 1` with its description left empty (`skill.enrich_error`), so it stops occupying the head of the pending queue, and it can be re-queued with `UPDATE job_skills SET ai_enriched = 0 WHERE name = '<skill>'`.

## Dependencies

- `commonlib` (shared library)
- `requests` (Ollama HTTP client)
- `transformers`, `torch`, `accelerate` (HuggingFace backend)
