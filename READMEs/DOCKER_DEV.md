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

**Ollama CPU/GPU:** `aienrich` service uses Ollama (runs by default).
**New CPU:** `aienrich3` service uses local fast CPU models (profile: `aiEnrich3`).
**New GPU:** `aienrichnew` service uses transformers pipeline (profile: `aiEnrichNew`).
**CV Matcher:** `aicvmatcher` service uses sentence transformers to rapidly match your cv (runs by default if configured in .env).

```bash
# Start core services (now includes aiEnrich)
docker-compose up -d

# If you want to use the alternative enrichment engines:
docker-compose --profile aiEnrich3 up -d aienrich3
docker-compose --profile aiEnrichNew up -d aienrichnew

# Ollama uses models from your host (defaults to ~/.ollama)
# For Windows, set in .env: OLLAMA_MODELS_PATH=C:/Users/YOUR_USERNAME/.ollama
# No need to pull models again - they're already available!

# Test Ollama connection
curl http://localhost:11434/api/tags
```

## With Scrapper

NOT TESTED YET!!!

```bash
# Start scrapper service
docker-compose --profile scrapper up -d scrapper

# Or run scrapper manually (one-time execution)
docker-compose run --rm scrapper
```

## All Services
```bash
# Start everything
docker-compose --profile ai-services --profile scrapper up -d
```

## Service URLs
- **Web (React)**: http://localhost:5173
- **Backend (FastAPI)**: http://localhost:8000/docs
- **Viewer (Streamlit)**: http://localhost:8501
- **MySQL**: localhost:3306
- **Ollama**: http://localhost:11434

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
