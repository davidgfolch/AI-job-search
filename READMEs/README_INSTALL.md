# Setup Guide

## System Requirements

- **Python**: 3.10 or newer is required (3.11 recommended).
  - Python 3.12 has incompatibilities with some libraries used.
  - **Install Python 3.11** — it satisfies the 3.10 baseline of every module (all modules declare `requires-python >=3.10,<3.13`, or `<3.14` for `commonlib`/`backend`/`scrapper`/`cron`).
- **Node.js**: LTS version (for `apps/web`).
- **Docker**: For running services in containers.
- **Ruff**: Optional locally, required by CI. Installed once for the whole repo with `uv tool install ruff` (step 7.3).
- **pre-commit**: Optional locally. Installs the commit hooks that run the same ruff and ESLint rules (step 7.4).

`scripts/install.sh` (Linux) / `scripts/install.bat` (Windows) automate the app dependencies, the shared host tools (Crawlee, Ruff, CodeGraph) and the default Ollama model pull. They need Python, Poetry, uv and npm on `PATH`, so install those first (steps 1–4) and run the script from a **new** terminal. The steps below remain the manual path for the pieces you prefer to do yourself.

## Package Managers

This project uses different package managers for different components:

- **Poetry**: Used by `apps/scrapper`, `apps/commonlib`.
- **uv**: Used by `apps/backend`, `apps/aiEnrich`, `apps/aiEnrichSkill`, `apps/aiCvMatcher`, `apps/cron`, and `apps/aiFormFiller`.
- **npm**: Used by `apps/web` and `apps/e2e`.

## Installation Steps

> **VS Code**: open `.vscode/AI-job-search.code-workspace` after installation. The workspace picks each app's `.venv`; the root `pyproject.toml` (not required to run or deploy) supplies the shared environment, the linting tools and the cross-module imports such as `commonlib`.

### 1. Install Python 3.11

Install **3.11** first (see System Requirements for why 3.11 and not 3.12).

**Windows 11:**

```powershell
winget install Python.Python.3.11
# or download the installer from https://www.python.org/downloads/ and tick
# "Add python.exe to PATH" during setup
```

**Linux (Debian/Ubuntu):**

```bash
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3-pip
# or use your distro's package manager, pyenv, or the installer from python.org
```

Verify in a **new** terminal:

```bash
python --version    # Windows
python3 --version   # Linux
```

### 2. Install Poetry (Python)

Poetry is used by `apps/scrapper` and `apps/commonlib`.

```bash
# Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# Linux/Mac
curl -sSL https://install.python-poetry.org | python3 -
```

### 3. Install uv (Python)

Required for `apps/backend`, `apps/aiEnrich`, `apps/aiEnrichSkill`, and `apps/aiCvMatcher`.

```bash
# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 4. Install Node.js & npm

Download and install from [nodejs.org](https://nodejs.org/).

### 5. Install GitHub CLI (recommended)

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

### 6. Install Ollama & required models

> **Note**: If you are using Docker, you do not need to install Ollama manually — add the `ollama` profile to run it containerized: `docker-compose --profile ollama up -d` (see [DOCKER_DEV.md](DOCKER_DEV.md)). If Ollama is already installed on your host, skip that: the AI modules auto-detect it and the `ollama` container is opt-in.

> **No-Ollama alternative**: if you plan to use the `openrouter` backend for `aiEnrich` (`AI_ENRICH_BACKEND=openrouter` in `.env`, see [apps/aiEnrich/README.md](../apps/aiEnrich/README.md)), you can skip Ollama entirely for that module — you only need an OpenRouter API key in `.env.secrets`. Ollama is still required by `aiEnrichSkill` (default backend `ollama`) unless it is also switched off.

Download and install from [ollama.com/download](https://ollama.com/download).

Run the following command to pull the models used by the AI modules:

```bash
# Required: default model for aiEnrich and aiEnrichSkill
ollama pull qwen2.5:3b

# Optional alternatives (recommended in apps/aiEnrich/README.md)
ollama pull phi3.5:3b
ollama pull llama3.2:1b
```

If you are running the Dockerized Ollama server (`docker-compose up -d ollama`), pull the models through the container instead:

```bash
docker exec ai-job-search-ollama ollama pull qwen2.5:3b
```

### 6.1 ISP blocking the Ollama registry (e.g. Movistar)

Some ISPs (e.g. Movistar) block or time out the model download host `r2.cloudflarestorage.com` (Cloudflare R2), so `ollama pull` hangs and fails with `dial tcp ...:443: i/o timeout`. Pull the same models from HuggingFace instead and alias them to the expected names:

```bash
# qwen2.5:3b (aiEnrich / aiEnrichSkill default)
ollama pull hf.co/Qwen/Qwen2.5-3B-Instruct-GGUF:q4_k_m
ollama cp hf.co/Qwen/Qwen2.5-3B-Instruct-GGUF:q4_k_m qwen2.5:3b
ollama rm hf.co/Qwen/Qwen2.5-3B-Instruct-GGUF:q4_k_m   # alias shares the same files; keep the list clean

```

The `ollama rm` removes the temporary HuggingFace tag (it shares the same blobs, so no space is freed/lost).

For the Dockerized server, prefix each command with `docker exec ai-job-search-ollama ollama`.

The helper install script picks this path automatically when `r2.cloudflarestorage.com` is unreachable; set `OLLAMA_PULL_SOURCE=hf` to force it.

### 7. Install Crawlee (source-page analysis)

Required by the `crawlee-page-analyst` agent skill to analyze a source page after a site/DOM redesign and produce scrapper-change requirements before selectors are edited (see [AGENTIC_SDLC.md](AGENTIC_SDLC.md)).

```bash
uv tool install "crawlee[all]"
```

> If you use `PlaywrightCrawler` and the browser binaries are missing, run `playwright install chromium` once.

### 7.1 Install Google Chrome & system libraries (scrapper)

The scrapper runs natively on the host — it is **not** a Docker service. Launch it with
`apps/scrapper/run.sh` (Linux/Mac) or `apps/scrapper/run.bat` (Windows), which run
`python -m scrapper.main` through Poetry. It therefore needs Google Chrome on the host;
ChromeDriver itself is downloaded automatically by `undetected-chromedriver`.

**Windows:** install Google Chrome from https://www.google.com/chrome/.

**Linux (Debian/Ubuntu):** install Chrome and the libraries it needs to run headless:

```bash
wget -q -O /tmp/google-chrome-key.pub https://dl-ssl.google.com/linux/linux_signing_key.pub
sudo gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg /tmp/google-chrome-key.pub
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt-get update
sudo apt-get install -y google-chrome-stable \
    gcc wget gnupg unzip curl ca-certificates \
    fonts-liberation libasound2 libatk-bridge2.0-0 libatk1.0-0 libatspi2.0-0 \
    libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 libnspr4 libnss3 \
    libwayland-client0 libxcomposite1 libxdamage1 libxfixes3 libxkbcommon0 \
    libxrandr2 xdg-utils
```

### 7.2 Install CodeGraph (default code intelligence)

[CodeGraph](https://github.com/colbymchenry/codegraph) is installed by its official installer, then wired into the detected agents with a local index:

```bash
# Linux/Mac
curl -fsSL https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.sh | sh

# Windows (PowerShell)
powershell -Command "irm https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.ps1 | iex"

# Then wire it into the detected agents and build this project's index
codegraph install --yes --init
```

CodeGraph is the default way to explore the codebase, for humans and agents alike: prefer `codegraph explore "<question>"` / `codegraph node <symbol>` over grepping or reading whole files. See [AGENTIC_SDLC.md](AGENTIC_SDLC.md#codegraph-code-intelligence) for the workflow and `.claude/skills/codegraph/SKILL.md` for the command reference.

### 7.3 Install Ruff (Python static analysis)

[Ruff](https://docs.astral.sh/ruff/) is the Python linter used by the `static-analysis`
CI gate. It is a single zero-dependency binary installed **once for the whole repo** —
no app needs it in its own virtual environment:

```bash
uv tool install ruff
```

`scripts/lint.sh` falls back to `uvx ruff` when the binary is not on `PATH`, so the gate
runs either way. Verify the install and run the gate:

```bash
ruff --version
./scripts/lint.sh python
```

The configuration lives in the root [`ruff.toml`](../ruff.toml) and covers every
Python app. See
[README_DEVELOPMENT.md#static-analysis](README_DEVELOPMENT.md#static-analysis) for
the rules in force.

### 7.4 Install pre-commit (optional, local commit hooks)

[pre-commit](https://pre-commit.com/) runs the same ruff and ESLint rules on the
changed files before each commit, so a finding is caught locally instead of in
the pipeline:

```bash
pip install pre-commit
pre-commit install
```

Optional: the `static-analysis` CI gate enforces the same rules either way. Details,
including the `npm install` prerequisite of the `apps/web` and `apps/e2e` ESLint hooks:
[README_DEVELOPMENT.md#pre-commit-hooks](README_DEVELOPMENT.md#pre-commit-hooks).

### 8. Install Project Dependencies

You can use the helper script in the project root:

```bash
./scripts/install.sh # or .\scripts\install.bat
```

> **Note**: If you run the web app via Docker, its image auto-detects changed `package-lock.json` and reinstalls `node_modules` on start (see `apps/web/docker-entrypoint.sh`), so `docker-compose up -d --build web` after a dependency change is enough. See [DOCKER_DEV.md](DOCKER_DEV.md).

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

Follow instructions in [apps/aiEnrich/README.md](../apps/aiEnrich/README.md), [apps/aiEnrichSkill/README.md](../apps/aiEnrichSkill/README.md), or [apps/aiCvMatcher/README.md](../apps/aiCvMatcher/README.md).

### 8.1 Uninstall Project Dependencies

`scripts/uninstall.bat` (Windows) / `scripts/uninstall.sh` (Linux) remove what the
install script created — virtual environments, `node_modules`, caches and ignored
lock files — through an interactive menu, and never touch `git`-tracked files,
`.env` / `.env.secrets` or the `data/` folders.

```bash
./scripts/uninstall.sh # or .\scripts\uninstall.bat
```

Ollama models are **not** removed: they live inside the Ollama server, not the project.

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
