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
| `.env` / `.env.secrets` | Bind-mounted (`./.env:/app/.env`), never baked, so **no rebuild**. Most values hot-reload in-process (below) |
| Source code (`apps/*` `.py`/`.tsx`) | Hot reload (backend uvicorn `--reload`, web Vite HMR) or `restart`; no rebuild |

Both `.env` and `.env.secrets` are bind-mounted into every build service, so editing
them never needs a rebuild. `commonlib.environmentUtil` re-reads them when their mtime
changes, so edited values apply without a restart, **except** for values captured once
at import (`metrics_collector.METRICS_FILE`, the `aiEnrichSkill`
`llm_client.MODEL_ID`, `cron/config.py`) — those need a `restart` (still no rebuild).
Values injected by Compose `environment:` outrank the dotenv files and are never
clobbered by a `.env` edit.

## Layer caching

Each Dockerfile copies dependency manifests, runs `uv sync --no-install-project`, then
copies the application source and runs `uv sync`. A source-only edit therefore reuses
the cached dependency layer. Keep that order, and keep `COPY apps/commonlib` before any
`uv sync` — commonlib is an editable path dependency and must be present to resolve.

## Dependency-refresh caveats

- **venv-volatile services** (`aienrich`, `aienrichskill`,
  `aicvmatcher`, `aiformfiller`, `cron`): their `.venv` lives in an
  **anonymous volume that survives rebuilds** — a dep bump with `--build` alone can
  keep running stale packages. Refresh with `docker compose rm -sfv <svc>` then
  `docker compose up -d --build <svc>`.
- `backend` sets `UV_PROJECT_ENVIRONMENT=/app/venv`, which is baked into
  the image rather than mounted, so it refreshes cleanly on rebuild.
- `web` self-heals: `apps/web/docker-entrypoint.sh` hash-checks `package-lock.json`
  and re-runs `npm ci` on mismatch.

Scrapper runs natively on the host (`apps/scrapper/run.sh`), not in Docker.
