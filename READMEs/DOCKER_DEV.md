# Quick Start Commands for Docker Development

## Profiles

The `docker-compose.yml` defines several service profiles to control which containers start:

| Profile        | Services                          | Description                      |
| -------------- | --------------------------------- | -------------------------------- |
| _(default)_    | `mysql_db`, `backend`, `web`, `aicvmatcher`, `aiformfiller`, `mongo_db`, `cron`, `prometheus`, `grafana` | Unprofiled core services (always start) |
| `ollama`       | `ollama`                          | Containerized Ollama server (opt-in; see the note below) |
| `aienrich`     | `aienrich`                        | Ollama AI enrichment             |
| `aiEnrichSkill`| `aienrichskill`                   | AI skill enrichment (Ollama & HuggingFace) |

## Core Services (Backend + Web)
```bash
# Start core services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

> **Service discovery:** in-container clients are pinned to their compose service names (`COMMONLIB_DB_HOST=mysql_db`, `MONGO_URI=mongodb://mongo_db:27017/`, `COMMONLIB_DB_DISCOVERY=False`), so a container start never triggers a LAN scan; host-native apps and other machines use the shared fallback chain. The scan result is cached in `./data/discovery/cache.json`, which every service mounts. Workers call `wait_for_db()` at startup instead of exiting when MySQL is not up yet (compose only gates the first start). Chains, `.env` pins and subnets: [Distributed execution & LAN service auto-discovery](DISTRIBUTED_EXECUTION.md).

## Distributed execution

Everything runs on one machine by default; the scrapper, the UI or the AI workers can also run on other machines, and LAN auto-discovery fills the gaps. Topologies, fallback order, `.env` pins and the Ollama host/container/LAN setup are documented once in [Distributed execution & LAN service auto-discovery](DISTRIBUTED_EXECUTION.md).

## With AI Services (AI Enrichment + Ollama)

**Ollama CPU/GPU:** `aienrich` service uses Ollama by default (profile: `aienrich`). Set `AI_ENRICH_LLM_BACKEND=openrouter` in `.env` to use OpenRouter cloud models instead (no Ollama needed for aienrich).
**Skill enrichment:** `aienrichskill` service enriches the `job_skills` table with Ollama or HuggingFace (profile: `aiEnrichSkill`).
**Live provider switch:** both workers read their provider from `.env` on every cycle, so the independent **Settings → LLM Providers** selectors in the web UI take effect without a container restart. Container healthchecks follow the live provider too.
**CV Matcher:** `aicvmatcher` service uses sentence transformers to rapidly match your cv (runs by default if configured in .env).

> Note: the `ollama` service is **opt-in** (`--profile ollama`) and no module hard-depends on it, so it is never started implicitly - useful when Ollama already runs on your host or on another LAN machine. Server resolution and the probe/caching behavior: [Distributed execution & LAN service auto-discovery](DISTRIBUTED_EXECUTION.md#ollama-host-container-or-another-lan-machine).

> **Windows 11 / Docker Desktop:** no Windows Defender change is needed while the workers and Ollama run in the same compose project - `aienrich`/`aienrichskill` default to `AI_ENRICH_OLLAMA_BASE_URL=http://ollama:11434` and reach the container by name on the compose network, and the published `11434:11434` covers the host itself (`localhost:11434`, `host.docker.internal:11434`). Allow inbound TCP 11434 only when *other machines* must reach this PC's Ollama (Private network profile, or as admin: `New-NetFirewallRule -DisplayName "Ollama" -Direction Inbound -Protocol TCP -LocalPort 11434 -Action Allow`), then verify from that machine with `Test-NetConnection <windows-ip> -Port 11434`.
>
> Docker Desktop exposes no GPU to containers by default, so containerized Ollama is CPU-only: set `COMMONLIB_OLLAMA_PROBE_TIMEOUT` higher (e.g. `120`) so a cold model load is not mistaken for a stalled runner, and keep the model warm with `OLLAMA_KEEP_ALIVE` (e.g. `30m`) in the `ollama` service environment to avoid reloading it between jobs.

```bash
# Start core services
docker-compose up -d

# Add the AI enrichment module you want
docker-compose --profile aienrich up -d aienrich
docker-compose --profile aiEnrichSkill up -d aienrichskill

# Only if you want Ollama containerized too (skip it if Ollama runs on the host):
docker-compose --profile ollama --profile aienrich up -d

# Ollama uses models from your host (defaults to ~/.ollama)
# For Windows, set in .env: OLLAMA_MODELS_PATH=C:/Users/YOUR_USERNAME/.ollama

# Test Ollama connection (URL defaults to centralized `OLLAMA_HOST_BASE_URL` in commonlib; unreachable configured URLs fall back to the host server)
curl <Ollama-URL>/api/tags
```

Model pull (including the Dockerized case and the HuggingFace fallback for ISPs that block the Ollama CDN): [README_INSTALL.md](README_INSTALL.md#6-install-ollama--required-models).

## Host-native apps

The scrapper always runs on the host; the backend, web and AI workers can too for development. Each app has a runner in its own directory, invoked from the repository root (`run.bat` on Windows):

| App | Runner |
|-----|--------|
| Scrapper | `./apps/scrapper/run.sh [platform]` |
| Backend | `./apps/backend/run.sh` |
| Web | `./apps/web/run.sh` |
| aiEnrich | `./apps/aiEnrich/run.sh` |
| aiEnrichSkill | `./apps/aiEnrichSkill/run.sh` |
| aiFormFiller | `./apps/aiFormFiller/run.sh` |
| Cron | `./apps/cron/run.sh` |

`apps/aiCvMatcher` has no runner: start it with Docker (`docker-compose up -d aicvmatcher`) or `uv run aicvmatcher` from `apps/aiCvMatcher`. The scrapper needs Google Chrome and its system libraries on the host — see [README_INSTALL.md](README_INSTALL.md#71-install-google-chrome--system-libraries-scrapper). Per-module flags and configuration: each `apps/<module>/README.md`.

## All Services
```bash
# Start the core services plus every AI enrichment profile
docker-compose --profile aienrich --profile aiEnrichSkill up -d
```

## Service URLs
- **Web (React)**: http://localhost:5173
- **Backend (FastAPI)**: http://localhost:8000/docs
- **MySQL**: localhost:3306
- **Ollama**: `OLLAMA_HOST_BASE_URL` (centralized in `commonlib`); resolved automatically from the configured URL, the Docker/host fallbacks or the LAN (see [Distributed execution & LAN service auto-discovery](DISTRIBUTED_EXECUTION.md#ollama-host-container-or-another-lan-machine))

## Development Tips
- Code changes are automatically detected (hot-reload enabled)
- Backend: Uvicorn auto-reloads on Python file changes
- Web: Vite HMR refreshes browser on code changes

## Web: backend discovery and reconnects
The `web` service resolves the backend API when it starts and keeps watching it:

- It waits for the backend to answer `/health` before serving (bounded by `BACKEND_WAIT_TIMEOUT_SECONDS`, default 120). After a host reboot every container starts in parallel, so this wait is what keeps the API proxy from pointing at a dead target.
- Candidates: `http://backend:8000` → `http://host.docker.internal:8000` → `http://localhost:8000`. Compose pins the first one in Docker (`BACKEND_URL=http://backend:8000`, `BACKEND_DISCOVERY=False`), so the container never scans the LAN. The `host.docker.internal` alias is mapped through `extra_hosts: host.docker.internal=host-gateway`, so the containerized web also reaches a backend running on the host.
- A watchdog probes the current target every `BACKEND_CHECK_INTERVAL_SECONDS` (default 10) and, after `BACKEND_MAX_RETRIES` (default 3) failures, resolves the backend again and retargets the live proxy.
- The web healthcheck asserts the API through the proxy (`/api/system/timezone`), so a broken proxy reports the container as unhealthy instead of healthy.

## Troubleshooting
```bash
# Rebuild after dependency changes
docker-compose build

# Rebuild specific service
docker-compose build backend

# View service logs
docker-compose logs -f backend

# Restart a service
docker-compose restart backend

# Clean rebuild of the images (keeps the named volumes and their data)
docker-compose build --no-cache
docker-compose up -d
```

> **Warning**: do **not** use `docker-compose down -v` as a "clean" step — it deletes every named volume of the project, including your Mongo data (`ai_job_search_mongo_data`) and MySQL data. To reset a single volume, remove only that volume (see below).

### Web container: stale `node_modules`

The web container keeps its installed dependencies in the named Docker volume
`web_node_modules` (mounted at `/app/node_modules`). Because that volume persists
across rebuilds and recreates, a plain `docker-compose up -d --build web` after a
dependency change can keep running the **old** package versions.

The web image ships an entrypoint (`apps/web/docker-entrypoint.sh`) that
compares `package-lock.json` against a hash marker stored inside `node_modules`
and re-runs `npm ci` only when they differ. So after a dependency update you can
simply rebuild and restart:

```bash
docker-compose up -d --build web
```

The entrypoint detects the changed lockfile and reinstalls the fresh
`node_modules` automatically — no manual volume cleanup needed. It logs
`[web-entrypoint] Dependencies changed... Running npm ci...` when it does.

Optional: for a full clean reset (e.g. corrupted `node_modules`), stop the
container and drop only that volume:

```bash
docker compose rm -sf web
docker volume rm ai_job_search_web_node_modules
docker compose up -d --build web
```


## Related Documentation

- **Development Guide**: [README_DEVELOPMENT.md](README_DEVELOPMENT.md)
- **Installation Guide**: [README_INSTALL.md](README_INSTALL.md)
- **Contribution Guide**: [README_CONTRIBUTE.md](README_CONTRIBUTE.md)
