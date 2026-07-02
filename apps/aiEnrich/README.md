# AI Job Enrichment

Job data enrichment service using Ollama LLMs.

## Overview

This application enriches job data (e.g., extracting salary, technologies, modality) using Ollama LLMs directly via HTTP API.

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

### LLM Model Selection

The default model is `ollama/qwen2.5:3b` (optimized for CPU inference). To change the model, set the `AI_ENRICH_OLLAMA_MODEL` environment variable in your `.env` file:

```bash
AI_ENRICH_OLLAMA_MODEL=ollama/phi3.5:3b
```

> or change it in http://localhost:5173/settings (docker with web/backend must be running, see [DOCKER_DEV.md](../READMEs/DOCKER_DEV.md))

**Recommended models for CPU-only inference:**

| Model | Speed | Accuracy |
|-------|-------|----------|
| `ollama/qwen2.5:3b` | Fast | Good |
| `ollama/phi3.5:3b` | Very Fast | Moderate |
| `ollama/llama3.2:1b` | Fastest | Lower |

Make sure the model is pulled in Ollama:
```bash
ollama pull qwen2.5:3b
```
