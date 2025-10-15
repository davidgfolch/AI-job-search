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
python -m pip install --upgrade pip
python -m pip install -r requirements.txt  # Install dependencies
python -m pip install -e . # Install ai-job-search as a module in .venv (in editable mode)
```

If problems found installing mysql client library for Streamlit, follow this:

```bash
sudo apt-get install pkg-config python3-dev default-libmysqlclient-dev build-essential
```

## Install crewai
See [README_CREWAI.md](./README_CREWAI.md)

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

We are using a base `requirements.in` with main dependencies, and generating `requirements.txt` with pip-compile.

### Add main dependency

```bash
source .venv/bin/activate
python -m pip install selenium  # !!!! then manually add it in requirements.in

# Create requirements.txt dependency-tree from base dependencies in requirements.in
python -m pip install pip-tools
pip-compile requirements.in
```

### Upgrading existing dependencies

```bash
python -m pip list --outdated
python -m pip install --upgrade selenium
```

### Remove dependency

```bash
python -m pip uninstall selenium
# and remove it from requirements.in and...
pip-compile requirements.in # to generate requirements.txt
# to fully check, delete .venv and start a clean .venv
```

### Dependency tree check
```bash
python -m pip install pipdeptree
pipdeptree

python -m pip check # Check dependencies
```
