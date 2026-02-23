# AiJobSearch Crew

Welcome to the AiJobSearch Crew project, powered by [crewAI](https://crewai.com).

## Overview

This application uses a multi-agent AI system to enrich job data (e.g., extracting salary, technologies, modality) using LLMs (Ollama/OpenAI).

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

To run the agent in a continuous loop (monitoring the database for new jobs):

```bash
# Linux
./run.sh

# Windows
.\run.bat
```

### Manual Run (Dev)

To run the crew manually:

```bash
uv run crewai run
```

## Configuration

- **Agents**: Define your agents in `src/ai_job_search/config/agents.yaml`.
- **Tasks**: Define your tasks in `src/ai_job_search/config/tasks.yaml`.
- **CV Matching**: Enable by setting `AI_CV_MATCH=True` in `.env` and placing your CV in `apps/aiEnrich/cv/cv.txt`.

## Support

- [crewAI Documentation](https://docs.crewai.com)
- [GitHub Repository](https://github.com/joaomdmoura/crewai)
