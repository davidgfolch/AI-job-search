# Setup Guide

## System Requirements

- **Python**: 3.10 required, except `apps/aiEnrich3`, which requires 3.11 (its locked `onnxruntime` has no 3.10 wheels).
  - `apps/aiEnrich3/.python-version` pins `3.11.14`; `uv` downloads and uses that interpreter automatically on `uv sync`.
  - Python 3.12 has incompatibilities with some libraries used.
  - **Install Python 3.11** — it is the only single version that satisfies both the 3.10 baseline and the 3.11 requirement of `apps/aiEnrich3` (all modules declare `requires-python >=3.10,<3.13`, or `<3.14` for `commonlib`/`backend`/`scrapper`/`cron`).
- **Node.js**: LTS version (for `apps/web`).
- **Docker**: For running services in containers.

> **Prerequisites for the install scripts**: `scripts\install.bat` (Windows) and
> `scripts/install.sh` (Linux) call `poetry` and `uv`, both of which need Python on `PATH`.
> On a fresh Windows 11 or Linux machine, install Python 3.11, Poetry, and uv first
> (steps 1-3 below), then run the script from a **new** terminal so `PATH` picks them up.

## Package Managers

This project uses different package managers for different components:

- **Poetry**: Used by `apps/scrapper`, `apps/commonlib`.
- **uv**: Used by `apps/backend`, `apps/aiEnrich`, `apps/aiEnrich3`, `apps/aiEnrichNew`, `apps/aiEnrichSkill`, `apps/aiCvMatcher`, `apps/cron`, and `apps/aiFormFiller`.
- **npm**: Used by `apps/web` and `apps/e2e`.

## Installation Steps

> **Note**: For the best development experience in VS Code, open the `.vscode/AI-job-search.code-workspace` file after installation. This ensures the correct Python interpreters are selected for each app.

### 1. Install Python 3.11

`scripts\install.bat` (Windows) and `scripts/install.sh` (Linux) call `poetry` and `uv`, both of which need a Python interpreter on `PATH` — install Python **3.11** first (see System Requirements for why 3.11 and not 3.12).

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

Required for `apps/backend`, `apps/aiEnrich`, `apps/aiEnrich3`, `apps/aiEnrichNew`, and `apps/aiCvMatcher`.

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

> `scripts/install.sh` installs commonlib first, then resolves the Ollama server with the same fallback chain the AI modules use (`commonlib.ollama_client.resolve_ollama_url` over `commonlib.ollama_config.get_configured_ollama_url()`: the configured URL, then `host.docker.internal`, `localhost`, the `ollama` compose service, and finally a LAN scan on port 11434; an `OLLAMA_HOST` already set in the shell is tried first). The resolved URL is exported as `OLLAMA_HOST`, so `qwen2.5:3b` (the AI modules' default; `qwen2.5-coder:7b` is only pulled when the graphify tooling is re-enabled) is pulled from that host — including a server that lives on another machine in the LAN — through the local `ollama` CLI when available, through `docker exec ai-job-search-ollama ollama` when the resolved host is the compose service, or directly against the host's Ollama HTTP API (`POST /api/pull`) when neither a local CLI nor a container exists. `scripts/install.bat` (Windows) resolves the same way and pulls via the local CLI, the container, or the host's HTTP API. Every step that needs a reachable server — the model pulls, and the graphify setup/indexing steps if you re-enable them — is best-effort: an unreachable server prints a warning and the dependency install continues, so you can run the skipped step later by hand. Before downloading anything, both scripts check whether the model is already on the resolved server (`ollama show` through the CLI or the container, or `POST /api/show` when neither exists) and skip the pull when the tag is present — a model already on a shared host in the LAN is never downloaded again, even when the registry probe fails and the HuggingFace fallback would otherwise kick in.

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

# qwen2.5-coder:7b (graphify community naming)
ollama pull hf.co/bartowski/Qwen2.5-Coder-7B-Instruct-GGUF:Q4_K_M
ollama cp hf.co/bartowski/Qwen2.5-Coder-7B-Instruct-GGUF:Q4_K_M qwen2.5-coder:7b
ollama rm hf.co/bartowski/Qwen2.5-Coder-7B-Instruct-GGUF:Q4_K_M
```

The `ollama rm` removes the temporary HuggingFace tag (it shares the same blobs, so no space is freed/lost).

For the Dockerized server, prefix each command with `docker exec ai-job-search-ollama ollama`.

The install scripts handle this automatically: `OLLAMA_PULL_SOURCE=auto` (default) probes `r2.cloudflarestorage.com` and falls back to HuggingFace + alias when it is unreachable, then removes the temporary tag. Force the source with `OLLAMA_PULL_SOURCE=ollama|hf`. The HuggingFace fallback only runs when the model is actually missing: both scripts first ask the server (`ollama show`, or `POST /api/show` on a remote host without a local CLI) and skip the download when `<model>` is already there, so an existing model is not pulled again just because the registry is blocked.

### 7. Install Crawlee (source-page analysis)

Required by the `crawlee-page-analyst` agent skill to analyze a source page after a site/DOM redesign and produce scrapper-change requirements before selectors are edited (see [AGENTIC_SDLC.md](AGENTIC_SDLC.md)).

```bash
uv tool install "crawlee[all]"
```

> `scripts/install.sh` / `scripts/install.bat` install it automatically. If you use `PlaywrightCrawler` and the browser binaries are missing, run `playwright install chromium` once.

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

### 7.2 Install codegraph (agent code-graph tooling)

`scripts/install.sh` / `scripts/install.bat` install [colbymchenry/codegraph](https://github.com/colbymchenry/codegraph) best-effort via its official installer:

```bash
# Linux/Mac (from scripts/install.sh)
curl -fsSL https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.sh | sh

# Windows (from scripts/install.bat)
powershell -Command "irm https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.ps1 | iex"
```

The scripts then wire CodeGraph into the agents they detect (**opencode**, Claude Code, Cursor, …) and build this project's index in one non-interactive step:

```bash
codegraph install --yes --init
```

`--yes` writes the MCP server entry into the detected agents' global config, and `--init` creates the local `.codegraph/` index, which ships its own `.gitignore` so the SQLite database and runtime files are never committed. The agent keeps the graph fresh automatically afterwards.

Both the CLI install and the wiring/indexing are best-effort: if the installer is unreachable, or the `codegraph` launcher is not on `PATH` yet in the current shell (the installers update `PATH` for new terminals only), the scripts print a warning and the app dependency install continues. In that case open a new terminal and run `codegraph install --yes --init` in the repo root manually; on Windows the launcher lives at `%LOCALAPPDATA%\codegraph\current\bin\codegraph.cmd`.

> codegraph is separate from the repo's existing `graphify` tooling (which builds `graphify-out/`). They write to different directories and can coexist.

### 8. Install Project Dependencies

You can use the helper script in the project root:

```bash
./scripts/install.sh # or .\scripts\install.bat
```

> **Note**: The `install.*` scripts install dependencies locally. If you run the
> web app via Docker, its image auto-detects changed `package-lock.json` and
> reinstalls `node_modules` on start (see `apps/web/docker-entrypoint.sh`), so a
> simple `docker-compose up -d --build web` after a dependency change is enough.
> See [DOCKER_DEV.md](DOCKER_DEV.md) for details.

> **Note**: On Linux/macOS the script also prepares the folders it will log into
> (`data/logs`, `data/metrics` and `apps/*/data/{logs,metrics}`) and fixes their owner.
> The Docker containers run as root and create root-owned files in those bind mounts,
> which then blocks the host user from writing its own logs, so `install.sh` re-owns
> them with `sudo chown -R "$(id -u):$(id -g)" data apps/*/data` when it finds any
> (it prints the command instead when `sudo` is unavailable). On Windows run the
> equivalent by hand from an elevated shell; otherwise the apps report
> `logs.write_failed` once per path and drop the affected records.

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

### 8.1 Uninstall Project Dependencies

`scripts/uninstall.bat` (Windows) and `scripts/uninstall.sh` (Linux) remove what
`install.*` installed: virtual environments, `node_modules`, caches, and the
gitignored lock files. The script shows an interactive menu and several items
can be selected at once (only dependencies that are currently installed are
shown); only the selected apps (or the root project, or the
global Crawlee/graphify tools) are removed. No `git` command is run, and tracked
files, `.env` / `.env.secrets`, and the `data/` folders are never touched.

```bash
./scripts/uninstall.sh # or .\scripts\uninstall.bat
```

Removing an app deletes its `.venv`, `node_modules` for the web apps, pytest
coverage and bytecode caches, and the ignored lock files. Ollama models are **not**
removed: they live inside the Ollama server, not the project.

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
