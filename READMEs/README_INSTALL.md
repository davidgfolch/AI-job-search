# Setup Guide

## System Requirements

- **Python**: 3.10 required.
  - Python 3.12 has incompatibilities with some libraries used.
- **Node.js**: LTS version (for `apps/web`).
- **Docker**: For running services in containers.

## Package Managers

This project uses different package managers for different components:

- **Poetry**: Used by `apps/scrapper`, `apps/commonlib`.
- **uv**: Used by `apps/backend`, `apps/aiEnrich` and `apps/aiEnrichNew`.
- **npm**: Used by `apps/web`.

## Installation Steps

> **Note**: For the best development experience in VS Code, open the `AI-job-search.code-workspace` file after installation. This ensures the correct Python interpreters are selected for each app.

### 1. Install Poetry (Python)

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### 2. Install uv (Python)

Required for `apps/aiEnrich`.

```bash
# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. Install Node.js & npm

Download and install from [nodejs.org](https://nodejs.org/).

### 4. Install Ollama & llama3.2 model

Download and install from [ollama.com/download](https://ollama.com/download).

Run the following command to install the llama3.2 model:

```bash
ollama pull llama3.2
```

### 5. Install Project Dependencies

You can use the helper script in the project root:

```bash
./scripts/install.sh # or .\scripts\install.bat
```

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

**AI Enrich:**

Follow instructions in [apps/aiEnrich/README.md](../apps/aiEnrich/README.md).

## Configuration

1. Copy the example environment file:
   ```bash
   cp scripts/.env.example .env
   ```
2. Edit `.env` with your credentials and configuration.

## Database Setup

After starting the MySQL container (via docker-compose or script), verify the database is initialized.
If needed, manually import schema:

```bash
docker exec -i ai-job-search-mysql mysql -uroot -prootPass jobs < scripts/mysql/ddl.sql
```

## Database Backup & Restore

```bash
# backup
docker exec ai-job-search-mysql /usr/bin/mysqldump -u root --password=rootPass jobs > scripts/mysql/20251219_backup.sql

# restore
cat scripts/mysql/20251219_backup.sql | docker exec -i ai_job_search-mysql /usr/bin/mysql -uroot -prootPass jobs
```

## Related Documentation

- **Development Guide**: [README_DEVELOPMENT.md](README_DEVELOPMENT.md)
- **Docker Development**: [DOCKER_DEV.md](DOCKER_DEV.md)
- **Contribution Guide**: [README_CONTRIBUTE.md](README_CONTRIBUTE.md)
