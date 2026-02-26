# aiEnrichNew

This module performs AI-based enrichment of job data (extracting technologies, salary, modality, etc.) using **local Hugging Face models** directly via the `transformers` library.

It is designed to be a lightweight, free alternative to the `aiEnrich` module (which uses CrewAI/Ollama).

## Prerequisites

- [uv](https://github.com/astral-sh/uv) installed.
- A GPU is recommended for faster inference, but CPU works (slower).

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
# Run
uv run aienrichnew
```

## Configuration

- **Model**: Defaults to `Qwen/Qwen2.5-1.5B-Instruct` (defined in `src/aiEnrichNew/dataExtractor.py`).
- **Environment Variables**:
    - `AI_ENRICHNEW_EXTRACT_TIMEOUT_SECONDS`: (Optional) Timeout for extraction.
