# Setup

Use python <= 3.11, python 3.12 has incompatibility with Streamlit required libraries for mysql.

## Project dependencies setup

```bash
    # Create environment
    python -m venv .venv
    # Activate environment
    source .venv/bin/activate
    # Install dependencies
    pip install -r requirements.txt
```

If problems found installing mysqlclient library for Streamlit, follow this:

```bash
    sudo apt-get install pkg-config python3-dev default-libmysqlclient-dev build-essential
```

## Pre setup

```bash
    sudo apt install python3.11
    sudo apt install python3.11-venv
    python -m ensurepip --upgrade
    pip install crewai crewai-tools linkedin-api ....
    # pip freeze
```
