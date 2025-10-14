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
    sudo apt install python3.10-venv
    python -m ensurepip --upgrade
    ```

## Install project dependencies

```bash
# Create environment
python -m venv .venv
# Activate environment
source .venv/bin/activate  # linux
.\.venv\Scripts\activate   # windows
# Install dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
# Install ai-job-search as a module in .venv
python -m pip install -e .
```

If problems found installing mysql client library for Streamlit, follow this:

```bash
sudo apt-get install pkg-config python3-dev default-libmysqlclient-dev build-essential
```

## Setup credentials & other settings

Set your cretentials in `.env` file.
You have an `scripts/.env.example` you can copy:

```bash
cp scripts/.env.example .env
```

Then edit your `.env` file.

> NOTE: AiEnricher using OPENAI_API_KEY or GEMINI_API_KEY are not tested.

## Setup database

After executing for first time `docker-compose up` or `docker compose up` or `./scripts/run_1_Mysql.sh`, you must create database tables with the ddl script:  `scripts/mysql/ddl.sql`

```bash
# Execute inside the docker container
docker exec -it ai-job-search-mysql_db-1 bash
mysql -uroot -prootPass jobs < docker-entrypoint-initdb.d/ddl.sql
```

[Mysql docker doc reference](https://hub.docker.com/_/mysql)

--------------

## Database backup



## Managing dependencies

### Add libraries

```bash
source .venv/bin/activate
pip install streamlit-aggrid
python -m pip freeze > requirements.txt
```

### Check dependencies

```bash
python -m pip check
python -m pip install langchain --upgrade
```
