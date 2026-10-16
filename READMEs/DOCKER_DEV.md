# Quick Start Commands for Docker Development

## Core Services (Backend + Web + Viewer)
```bash
# Start core services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## With AI Services (AI Enrichment + Ollama)

**Ollama CPU/GPU:** `aienrich` service uses Ollama by default (profile: `aienrich`). Set `AI_ENRICH_BACKEND=openrouter` in `.env` to use OpenRouter cloud models instead (no Ollama needed for aienrich).
**New CPU:** `aienrich3` service uses local fast CPU models (profile: `aiEnrich3`).
**New GPU:** `aienrichnew` service uses transformers pipeline (profile: `aiEnrichNew`).
**CV Matcher:** `aicvmatcher` service uses sentence transformers to rapidly match your cv (runs by default if configured in .env).

> Note: the `ollama` service is **opt-in** (`--profile ollama`) and no module hard-depends on it, so it is never started implicitly - useful when Ollama already runs on your host. The Ollama-backed modules probe the configured URL, then `host.docker.internal`, `localhost` and `ollama:11434`, and use the first one that answers. Each job is only sent to a server that answers a one-token generation probe (`COMMONLIB_OLLAMA_PROBE_TIMEOUT`, default 30s), so a stalled runner is skipped instead of blocking the whole job timeout; that verdict is remembered per server for `COMMONLIB_OLLAMA_PROBE_CACHE_SECONDS` (default 300), so the following jobs go straight to inference instead of re-connecting every time. The workers take that URL from `.env` (`docker-compose.yml` only defaults to `http://ollama:11434` when it is unset), so pointing them at Ollama on your host or on another machine is `AI_ENRICH_OLLAMA_BASE_URL=http://<host>:11434` in `.env` plus a worker restart (`docker compose up -d --force-recreate aienrich aienrichskill`).

> **Windows 11 / Docker Desktop:** no Windows Defender change is needed while the workers and Ollama run in the same compose project - `aienrich`/`aienrichskill` default to `AI_ENRICH_OLLAMA_BASE_URL=http://ollama:11434` and reach the container by name on the compose network, and the published `11434:11434` covers the host itself (`localhost:11434`, `host.docker.internal:11434`). Allow inbound TCP 11434 only when *other machines* must reach this PC's Ollama (Private network profile, or as admin: `New-NetFirewallRule -DisplayName "Ollama" -Direction Inbound -Protocol TCP -LocalPort 11434 -Action Allow`), then verify from that machine with `Test-NetConnection <windows-ip> -Port 11434`.
>
> Docker Desktop exposes no GPU to containers by default, so containerized Ollama is CPU-only: set `COMMONLIB_OLLAMA_PROBE_TIMEOUT` higher (e.g. `120`) so a cold model load is not mistaken for a stalled runner, and keep the model warm with `OLLAMA_KEEP_ALIVE` (e.g. `30m`) in the `ollama` service environment to avoid reloading it between jobs.
>
> **Discovery stops at the Docker network:** inside a container the LAN sweep covers only the container's own subnets (e.g. `172.19.x`), so it finds sibling containers and the Docker gateway but *not* an Ollama on the physical LAN. Reaching a machine like `192.168.1.211` from a container therefore requires pinning `AI_ENRICH_OLLAMA_BASE_URL` (or running the worker with `network_mode: host`), even though the container can route to it.

```bash
# Start core services
docker-compose up -d

# Add the AI enrichment module you want
docker-compose --profile aienrich up -d aienrich
docker-compose --profile aiEnrich3 up -d aienrich3
docker-compose --profile aiEnrichNew up -d aienrichnew

# Only if you want Ollama containerized too (skip it if Ollama runs on the host):
docker-compose --profile ollama --profile aienrich up -d

# Ollama uses models from your host (defaults to ~/.ollama)
# For Windows, set in .env: OLLAMA_MODELS_PATH=C:/Users/YOUR_USERNAME/.ollama

# Pull the models required by aiEnrich / aiEnrichSkill.
# Non-dockerized (host Ollama):
ollama pull qwen2.5:3b # required default
# ollama pull phi3.5:3b  # optional faster alternative
# ollama pull llama3.2:1b # optional fastest alternative

# Dockerized (pull inside the container):
docker exec ai-job-search-ollama ollama pull qwen2.5:3b

# If your ISP blocks the Ollama model CDN (r2.cloudflarestorage.com, e.g. Movistar),
# `ollama pull` hangs with "dial tcp ... i/o timeout". Pull from HuggingFace
# instead and alias the model to the expected tag:
docker exec ai-job-search-ollama ollama pull hf.co/Qwen/Qwen2.5-3B-Instruct-GGUF:q4_k_m
docker exec ai-job-search-ollama ollama cp hf.co/Qwen/Qwen2.5-3B-Instruct-GGUF:q4_k_m qwen2.5:3b
docker exec ai-job-search-ollama ollama rm hf.co/Qwen/Qwen2.5-3B-Instruct-GGUF:q4_k_m   # temp tag shares the same files

# Test Ollama connection (URL defaults to centralized `OLLAMA_HOST_BASE_URL` in commonlib; unreachable configured URLs fall back to the host server)
curl <Ollama-URL>/api/tags
```

## Scrapper (runs on the host, not in Docker)

The scrapper is **not** a Docker service. Run it natively in a terminal:

```bash
./apps/scrapper/run.sh   # or .\apps\scrapper\run.bat on Windows
```

See [README_INSTALL.md](README_INSTALL.md#61-install-google-chrome--system-libraries-scrapper) for the required Chrome/system libraries.

## All Services
```bash
# Start the core services plus every AI enrichment profile
docker-compose --profile aienrich --profile aiEnrichNew --profile aiEnrichSkill --profile aiEnrich3 up -d
```

## Service URLs
- **Web (React)**: http://localhost:5173
- **Backend (FastAPI)**: http://localhost:8000/docs
- **Viewer (Streamlit)**: http://localhost:8501
- **MySQL**: localhost:3306
- **Ollama**: `OLLAMA_HOST_BASE_URL` (centralized in `commonlib`; modules fall back from the containerized `ollama:11434` to the host server)

## Development Tips
- Code changes are automatically detected (hot-reload enabled)
- Backend: Uvicorn auto-reloads on Python file changes
- Web: Vite HMR refreshes browser on code changes
- Viewer: Streamlit auto-reruns on file changes

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

# Clean rebuild
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Web container: stale `node_modules`

The web container keeps its installed dependencies in an anonymous Docker volume
(`/app/node_modules`). Because that volume persists across rebuilds, a plain
`docker-compose up -d --build web` after a dependency change can keep running the
**old** package versions.

The web image now ships an entrypoint (`apps/web/docker-entrypoint.sh`) that
compares `package-lock.json` against a hash marker stored inside `node_modules`
and re-runs `npm ci` only when they differ. So after a dependency update you can
simply rebuild and restart:

```bash
docker-compose up -d --build web
```

The entrypoint detects the changed lockfile and reinstalls the fresh
`node_modules` automatically — no manual volume cleanup needed. It logs
`[web-entrypoint] Dependencies changed... Running npm ci...` when it does.

Optional: for a full clean reset (e.g. corrupted `node_modules`), you can still
force it by removing the web container's anonymous volumes (named volumes such as
`mysql_data` are left untouched):

```bash
docker compose rm -sfv web && docker compose build web && docker compose up -d web
```

> **Warning**: do **not** use `docker-compose down -v` for this — it deletes all
> named volumes for the project too, including your MySQL database
> (`ai-job-search_mysql_data`).


## Related Documentation

- **Development Guide**: [README_DEVELOPMENT.md](README_DEVELOPMENT.md)
- **Installation Guide**: [README_INSTALL.md](README_INSTALL.md)
- **Contribution Guide**: [README_CONTRIBUTE.md](README_CONTRIBUTE.md)
