# aiEnrichSkill

Decoupled skill enrichment module supporting **Ollama** and **HuggingFace** backends.

Extracted from `aiEnrich` and `aiEnrichNew` — provides AI-based enrichment of `job_skills` table (description and category generation).

## Backends

| Backend | Env Value | Requirements |
|---------|-----------|-------------|
| Ollama (default) | `ollama` | Ollama server running (default URL centralized as `OLLAMA_DEFAULT_BASE_URL` in `commonlib`) |
| HuggingFace | `huggingface` | Local transformers, GPU recommended |

## Usage

### Windows
```cmd
run.bat
```

### Linux / Mac
```bash
./run.sh
```

### Manual
```bash
uv run aienrichskill
```

## Configuration

Set these in your `.env` or `.env.secrets`:

### General
- `AI_ENRICHSKILL_ENABLED` — Enable/disable (default: `True`)
- `AI_ENRICHSKILL_BACKEND` — Backend: `ollama` or `huggingface` (default: `ollama`)
- `AI_ENRICHSKILL_CATEGORIES` — Comma-separated skill categories (required)
- `AI_ENRICHSKILL_ENRICH_LIMIT` — Max skills per run (default: `10`)
- `AI_ENRICHSKILL_TIMEOUT` — Timeout per item in seconds (default: `90`)

### Ollama Backend
- `AI_ENRICHSKILL_OLLAMA_BASE_URL` — Ollama server URL (overrides centralized default `OLLAMA_DEFAULT_BASE_URL` in `commonlib`)
- `AI_ENRICHSKILL_OLLAMA_MODEL` — Model name (default: `ollama/qwen2.5:3b`)

Pull the default model before running:

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
       ├─ backend == "ollama"      → ollama_client.py + commonlib.process_skill_enrichment
       └─ backend == "huggingface" → llm_client.py + llm_utils.py batch processing
```

## Dependencies

- `commonlib` (shared library)
- `requests` (Ollama HTTP client)
- `transformers`, `torch`, `accelerate` (HuggingFace backend)
