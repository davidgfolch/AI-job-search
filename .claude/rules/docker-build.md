---
trigger: always_on
---

## Docker container bring-up: always `--build`

Bring up containers with `docker compose up -d --build <service>` (or the legacy
`docker-compose`). A PreToolUse hook (`.claude/hooks/docker-build.py`) and an opencode
plugin (`.opencode/plugins/docker-build.js`) silently inject `--build` into every
`docker compose up` command — do not strip it.

## When rebuilding is required (why)

| Changed | Action |
|---|---|
| Dependency manifests (`pyproject.toml`, `uv.lock`, `poetry.lock`, `package.json`, `package-lock.json`), Dockerfile, entrypoints, baked files | **Rebuild required** (`--build`) |
| `.env` / `.env.secrets` | Bind-mounted (`./.env:/app/.env`), so **restart** suffices; no rebuild |
| Source code (`apps/*` `.py`/`.tsx`) | Hot reload (backend uvicorn `--reload`, web Vite HMR) or `restart`; no rebuild |

## Dependency-refresh caveats

- **venv-volatile services** (`aienrich`, `aienrichnew`, `aienrichskill`,
  `aicvmatcher`, `aienrich3`, `aiformfiller`, `cron`): their `.venv` lives in an
  **anonymous volume that survives rebuilds** — a dep bump with `--build` alone can
  keep running stale packages. Refresh with `docker compose rm -sfv <svc>` then
  `docker compose up -d --build <svc>`.
- `backend` (`/app/venv`) and `scrapper` (system python, `virtualenvs.create false`)
  refresh cleanly on rebuild.
- `web` self-heals: `apps/web/docker-entrypoint.sh` hash-checks `package-lock.json`
  and re-runs `npm ci` on mismatch.