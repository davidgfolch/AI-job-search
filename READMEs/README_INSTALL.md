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

Follow each README (in order):

[packages/commonlib README.md](../packages/commonlib/README.md)

If problems found installing mysql client library for Streamlit, follow this:

```bash
sudo apt-get install pkg-config python3-dev default-libmysqlclient-dev build-essential
```

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
mysql -uroot -prootPass jobs < docker-entrypoint-initdb.d/backup.sql
```

[Mysql docker doc reference](https://hub.docker.com/_/mysql)

--------------

## Database backup

```bash
docker exec ai_job_search-mysql_db-1 /usr/bin/mysqldump -u root --password=rootPass jobs > scripts/backup.sql
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

