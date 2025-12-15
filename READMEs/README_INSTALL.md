# Setup Guide

## System Requirements

- **Python**: 3.10 required.
  - Python 3.12 has incompatibilities with some libraries used.
- **Node.js**: LTS version (for `apps/web`).
- **Docker**: For running services in containers.

## Package Managers

This project uses different package managers for different components:

- **Poetry**: Used by `apps/backend`, `apps/scrapper`, `packages/commonlib`, and `apps/viewer`.
- **uv**: Used by `apps/aiEnrich` (CrewAI requirement).
- **npm**: Used by `apps/web`.

## Installation Steps

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

### 4. Install Project Dependencies

You can use the helper script in the project root:

```bash
./scripts/install.sh # or .\scripts\install.bat
```

Or install manually:

**Backend & Scrapper & Commonlib:**

```bash
cd packages/commonlib && poetry install && cd ../..
cd apps/backend && poetry install && cd ../..
cd apps/scrapper && poetry install && cd ../..
```

**Web Frontend:**

```bash
cd apps/web
npm install
cd ../..
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
docker exec -i ai-job-search-mysql_db-1 mysql -uroot -prootPass jobs < scripts/mysql/ddl.sql
```

## Database Backup & Restore

```bash
# backup
docker exec ai-job-search-mysql_db-1 /usr/bin/mysqldump -u root --password=rootPass jobs > scripts/mysql/backup.sql

# restore
cat scripts/mysql/backup.sql | docker exec -i ai_job_search-mysql_db-1 /usr/bin/mysql -uroot -prootPass jobs
```
