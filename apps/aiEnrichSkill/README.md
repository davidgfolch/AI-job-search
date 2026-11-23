# aiEnrichSkill

Decoupled skill enrichment module supporting **Ollama** and **HuggingFace** backends.

Extracted from `aiEnrich` — provides AI-based enrichment of `job_skills` table (description, category and learning-path links).

## Backends

| Backend | Env Value | Requirements |
|---------|-----------|-------------|
| Ollama (default) | `ollama` | Ollama server running (URL configured in `.env`; see [Ollama Backend](#ollama-backend)) |
| HuggingFace | `huggingface` | Local transformers, GPU recommended |

## Usage

### Docker (recommended)

```bash
# From the repository root; add --profile ollama when Ollama is containerized
docker-compose --profile aiEnrichSkill up -d aienrichskill
```

The worker auto-discovers its dependencies, so it runs unchanged on the host, in Docker or on another LAN machine. Workers stay
in Docker: to pin a remote Ollama set `AI_ENRICH_OLLAMA_BASE_URL=http://<ollama-ip>:11434` in `.env` (compose maps it to
`AI_ENRICHSKILL_OLLAMA_BASE_URL`), or use `auto` to scan the LAN. Chains, subnets and the Ollama-side `OLLAMA_HOST`/firewall
requirements: [Distributed execution & LAN service auto-discovery](../../READMEs/DISTRIBUTED_EXECUTION.md).

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
- `AI_ENRICHSKILL_NUM_CTX` — Context window sent to Ollama per request (default: sized from the prompt, capped at `32768`)
- `AI_ENRICHSKILL_REPEAT_PENALTY` — Repetition penalty for Ollama (default: `1.0`, disabled)

These Ollama knobs are shared with `aiEnrich` and are not module-scoped: the first of `AI_ENRICH_*` / `AI_ENRICHSKILL_*` that is set wins, so an `AI_ENRICH_NUM_CTX` in `.env` also applies here.

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

The model proposes links, and each candidate page is loaded and checked before persisting: only substantive pages actually about
the skill are kept, in documentation → tutorial/course → video order. Homepages, search/login/error pages, thin pages and dead
videos are dropped. Missing tiers can be filled from DuckDuckGo results (the search URL itself is never stored). If nothing
verifies, no links are stored, and existing user-curated links are never overwritten.

Learning paths are stored on `job_skills.learning_path` with each link's source (model, search, manual or legacy); older plain-string values are still read.
The column is in [scripts/mysql/ddl.sql](../../scripts/mysql/ddl.sql) and the stored shape in [commonlib/skill_learning_path.py](../commonlib/commonlib/skill_learning_path.py).

- `AI_ENRICHSKILL_LEARNING_PATHS` — Enable the whole feature (default: `True`). `False` removes the prompt section and disables the idle backfill.
- `AI_ENRICHSKILL_LEARNING_PATH_MAX` — Links requested/persisted per skill (default: `3`)
- `AI_ENRICHSKILL_LEARNING_PATH_BATCH` — Skills per idle backfill pass (default: `1`)
- `AI_ENRICHSKILL_LEARNING_PATH_TIMEOUT` — HTTP fetch/search timeout for link validation, in seconds (default: `5`). The links-only generation call uses `AI_ENRICHSKILL_TIMEOUT`.
- `AI_ENRICHSKILL_LEARNING_PATH_SEARCH` — Fill missing tiers with DuckDuckGo results verified by loading each page (default: `True`)
- `AI_ENRICHSKILL_LEARNING_PATH_SEARCH_RESULTS` — Search results inspected per missing tier (default: `10`)
- `AI_ENRICHSKILL_LEARNING_PATH_MAX_FAILURES` — Consecutive failures before the idle pass backs off (default: `3`)
- `AI_ENRICHSKILL_LEARNING_PATH_RETRY_SECONDS` — Backoff duration before one retry; a failed trial restarts the wait (default: `900`, 15 minutes)
- `AI_ENRICHSKILL_LEARNING_DOMAINS` — Comma-separated preferred domains that rank ahead of other verified pages (defaults to a
  built-in documentation/course/video list). A URL outside this list is still accepted when its loaded content is verified as
  being about the skill.

## Architecture

There are two enrichment passes: an interactive one triggered by a new skill or *Auto-fill with AI*, which produces description,
category and links, and a low-priority idle backfill for already-enriched skills with no learning paths. The backfill is
Ollama-only (the HuggingFace path writes links during the interactive pass), runs only while the model is free so real work
preempts it, and writes legitimate worker output to `job_skills`, so the container needs outbound HTTPS.

In containers the wait between idle cycles is silent and `docker-compose logs` shows one record per cycle; interactive terminals
keep the countdown. An unreachable Ollama is waited for instead of exiting (`AI_ENRICHSKILL_MAX_OLLAMA_FAILURES` controls when
the wait is announced). A skill Ollama answers for but cannot describe within `AI_ENRICHSKILL_TIMEOUT` is marked enriched with
an empty description; re-queue it with `UPDATE job_skills SET ai_enriched = 0 WHERE name = '<skill>'`.

## Dependencies

- `commonlib` (shared library)
- `requests` (Ollama HTTP client)
- `transformers`, `torch`, `accelerate` (HuggingFace backend)
