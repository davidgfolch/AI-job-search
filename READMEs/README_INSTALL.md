# Setup

Use python 3.10.

Python 3.12 has incompatibility with Streamlit required libraries for mysql,
and 3.11 incompatibility with other crewAi libraries.

## Prerequisites

- [Docker & docker-compose](https://docs.docker.com/compose/install/)
- [Local Ollama](https://github.com/davidgfolch/OpenAI-local-ollama-chat/blob/main/README_OLLAMA.md) (OPTIONAL, for AI enrichment)
- Python 3.10 & libraries:

```bash
sudo apt install python3.10
```

### Package managers install

#### Poetry (all modules except apps/aiEnrich)

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

#### UV (for apps/aiEnrich)

AiEnrich uses CrewAI framework, and CrewAI uses UV

> <https://docs.crewai.com/en/installation>

```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows
curl -LsSf https://astral.sh/uv/install.sh | sh  # Linux
uv tool update-shell
```

## Install project dependencies

In project root folder execute `./scripts/install.sh`

> If problems found installing mysql client library for Streamlit, follow this:
> `sudo apt-get install pkg-config python3-dev default-libmysqlclient-dev build-essential`

## Install crewai

> <https://docs.crewai.com/en/installation>

In `apps/crewAi` folder:

```bash
uv tool install crewai
uv tool list
```

> uv tool install crewai --upgrade

## Setup credentials & other settings

Set your cretentials in `.env` file.
You have an `scripts/.env.example` you can copy:

```bash
cp scripts/.env.example .env
```

Then edit your `.env` file.

## Setup database

After executing for first time `docker-compose up` or `docker compose up` or `./scripts/run_1_Mysql.sh`, you must create database tables with the ddl script:  `scripts/mysql/ddl.sql`

```bash
docker exec -it ai-job-search-mysql_db-1 bash
# Execute next lines inside the docker container
mysql -uroot -prootPass jobs < docker-entrypoint-initdb.d/ddl.sql
```

[Mysql docker doc reference](https://hub.docker.com/_/mysql)

--------------

## Database backup

```bash
# backup
docker exec ai-job-search-mysql_db-1 /usr/bin/mysqldump -u root --password=rootPass jobs > scripts/mysql/20251029_backup.sql
# restore
cat scripts/mysql/backup.sql | docker exec -i ai_job_search-mysql_db-1 /usr/bin/mysql -uroot -prootPass jobs
```

## Managing dependencies

This monorepo has a `packages/commonlib` shared for all `apps/*`

```bash
cd packages/commonlib && poetry install && cd ../..
cd apps/scrapper && poetry install && cd ../..
cd apps/viewer && poetry install && cd ../..
```
Then install [AiEnrich following it's readme](/apps/aiEnrich/README.md).


### Add main dependency

```bash
poetry add selenium
```

### Upgrading existing dependencies

```bash
poetry show --outdated
poetry update
```

### Remove dependency

```bash
poetry remove selenium
```

