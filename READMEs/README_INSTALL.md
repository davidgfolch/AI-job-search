# Setup Guide

## System Requirements

- **Python**: 3.10 required.
  - Python 3.12 has incompatibilities with some libraries used.
- **Node.js**: LTS version (for `apps/web`).
- **Docker**: For running services in containers.

## Package Managers

This project uses different package managers for different components:

- **Poetry**: Used by `apps/scrapper`, `apps/commonlib`.
- **uv**: Used by `apps/backend`, `apps/aiEnrich`, `apps/aiEnrich3`, `apps/aiEnrichNew`, and `apps/aiCvMatcher`.
- **npm**: Used by `apps/web`.

## Installation Steps

> **Note**: For the best development experience in VS Code, open the `.vscode/AI-job-search.code-workspace` file after installation. This ensures the correct Python interpreters are selected for each app.

### 1. Install Poetry (Python)

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### 2. Install uv (Python)

Required for `apps/backend`, `apps/aiEnrich`, `apps/aiEnrich3`, `apps/aiEnrichNew`, and `apps/aiCvMatcher`.

```bash
# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. Install Node.js & npm

Download and install from [nodejs.org](https://nodejs.org/).

### 4. Install GitHub CLI (recommended)

Required by the agent tooling to process Dependabot PRs (see the `dependabot-agent` skill in `.claude/skills/`, [AGENTIC_SDLC.md](AGENTIC_SDLC.md), and [README_GITHUB.md](README_GITHUB.md)).

```bash
# Windows
winget install GitHub.cli

# Linux/Mac
curl -fsSL https://cli.github.com/packages/install.sh | sh  # or use your distro's package manager
```

Then authenticate:

```bash
gh auth login
```

Verify with `gh auth status`.

### 5. Install Ollama & required models

> **Note**: If you are using Docker, you do not need to install Ollama manually. You can run `aiEnrich` and Ollama via `docker-compose up -d` (see [DOCKER_DEV.md](DOCKER_DEV.md)).

Download and install from [ollama.com/download](https://ollama.com/download).

Run the following command to pull the models used by the AI modules:

```bash
# Required: default model for aiEnrich and aiEnrichSkill
ollama pull qwen2.5:3b

# Optional alternatives (recommended in apps/aiEnrich/README.md)
ollama pull phi3.5:3b
ollama pull llama3.2:1b
```

> `scripts/install.sh` / `scripts/install.bat` also pull `qwen2.5-coder:7b` (graphify tooling) and `qwen2.5:3b` (AI modules) automatically, detecting whether Ollama is dockerized (pull via the `ai-job-search-ollama` container) or installed directly on the host.

If you are running the Dockerized Ollama server (`docker-compose up -d ollama`), pull the models through the container instead:

```bash
docker exec ai-job-search-ollama ollama pull qwen2.5:3b
```

### 5.1 ISP blocking the Ollama registry (e.g. Movistar)

Some ISPs (e.g. Movistar) block or time out the model download host `r2.cloudflarestorage.com` (Cloudflare R2), so `ollama pull` hangs and fails with `dial tcp ...:443: i/o timeout`. Pull the same models from HuggingFace instead and alias them to the expected names:

```bash
# qwen2.5:3b (aiEnrich / aiEnrichSkill default)
ollama pull hf.co/Qwen/Qwen2.5-3B-Instruct-GGUF:q4_k_m
ollama cp hf.co/Qwen/Qwen2.5-3B-Instruct-GGUF:q4_k_m qwen2.5:3b

# qwen2.5-coder:7b (graphify community naming)
ollama pull hf.co/bartowski/Qwen2.5-Coder-7B-Instruct-GGUF:Q4_K_M
ollama cp hf.co/bartowski/Qwen2.5-Coder-7B-Instruct-GGUF:Q4_K_M qwen2.5-coder:7b
```

For the Dockerized server, prefix each command with `docker exec ai-job-search-ollama ollama`.

The install scripts handle this automatically: `OLLAMA_PULL_SOURCE=auto` (default) probes `r2.cloudflarestorage.com` and falls back to HuggingFace + alias when it is unreachable. Force the source with `OLLAMA_PULL_SOURCE=ollama|hf`.

### 6. Install Project Dependencies

You can use the helper script in the project root:

```bash
./scripts/install.sh # or .\scripts\install.bat
```

> **Note**: The `install.*` scripts install dependencies locally. If you run the
> web app via Docker, its image auto-detects changed `package-lock.json` and
> reinstalls `node_modules` on start (see `apps/web/docker-entrypoint.sh`), so a
> simple `docker-compose up -d --build web` after a dependency change is enough.
> See [DOCKER_DEV.md](DOCKER_DEV.md) for details.

Or install manually:

**Commonlib, Backend & Scrapper:**

```bash
cd apps/commonlib && poetry install && cd ../..
cd apps/scrapper && poetry install && cd ../..
cd apps/backend && uv sync && cd ../..
```

**Web Frontend:**

```bash
cd apps/web && npm install && cd ../..
```

**AI Enrich and AI CV Matcher:**

Follow instructions in [apps/aiEnrich/README.md](../apps/aiEnrich/README.md), [apps/aiEnrich3/README.md](../apps/aiEnrich3/README.md), [apps/aiEnrichNew/README.md](../apps/aiEnrichNew/README.md), or [apps/aiCvMatcher/README.md](../apps/aiCvMatcher/README.md).

## Configuration

1. Copy the secrets template:
   ```bash
   cp scripts/.env.secrets.example .env.secrets
   ```
2. Edit `.env.secrets` with your credentials and `.env` with your configuration (create `.env` if needed).

## Database Setup

After starting the MySQL container (via docker-compose or script), verify the database is initialized.
If needed, manually import schema:

```bash
docker exec -i ai-job-search-mysql mysql -uroot -prootPass jobs < scripts/mysql/ddl.sql
```

## Database Backup & Restore

You can use the provided scripts in `scripts/mysql` to backup and restore the database. These scripts handle common issues like GTID warnings and secure password usage.

### Backup

```bash
# Bash
./scripts/mysql/backup.sh
```

```powershell
# Windows (CMD/PowerShell)
.\scripts\mysql\backup.bat
```

This will create a timestamped SQL file in `scripts/mysql/backups`.

### Restore

```bash
# Bash
./scripts/mysql/restore.sh scripts/mysql/backups/YYYYMMDD_HHMM_backup.sql
```

```powershell
# Windows (CMD/PowerShell)
.\scripts/mysql/restore.bat scripts/mysql/backups/YYYYMMDD_HHMM_backup.sql
```

> **Note**: The scripts automatically handle the MySQL password securely and suppress common warnings (GTID, etc).

## Related Documentation

- **Development Guide**: [README_DEVELOPMENT.md](README_DEVELOPMENT.md)
- **Docker Development**: [DOCKER_DEV.md](DOCKER_DEV.md)
- **Contribution Guide**: [README_CONTRIBUTE.md](README_CONTRIBUTE.md)
