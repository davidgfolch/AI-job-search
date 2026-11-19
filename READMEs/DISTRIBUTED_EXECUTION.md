# Distributed Execution & LAN Service Auto-Discovery

The default deployment is a single machine: `docker-compose up -d` starts the core services and every container reaches its dependencies by compose service name (`mysql_db`, `mongo_db`, `backend`, and the opt-in `ollama`). **No IPs need to be set in `.env`.**

From there the stack scales out without changing images: each service can run on the machine that suits it (scrapper on a scraper box, UI only on a client, AI workers anywhere), and any dependency that is not on the compose network is resolved through the shared LAN fallback chain.

## How a dependency is resolved

Every client tries the configured value first, then the compose/host fallbacks, then (where enabled) a cached LAN scan:

| Dependency | Configured with | Fallback order |
|---|---|---|
| MySQL | `COMMONLIB_DB_HOST` (single IP, CIDR, range or CSV; `auto` scans first) | configured host(s) → `mysql_db` → `host.docker.internal` → `127.0.0.1` → LAN scan on 3306 |
| MongoDB | `MONGO_URI` | configured URI → `mongo_db` → `host.docker.internal` → `127.0.0.1` → LAN scan on 27017 |
| Backend API | `BACKEND_URL` | when set, that URL only; when unset `backend:8000` → `host.docker.internal:8000` → `localhost:8000` (reverse on the host), then a LAN scan if `BACKEND_DISCOVERY=True` |
| Ollama | `AI_ENRICH_OLLAMA_BASE_URL` (`auto` scans directly) | configured URL → `host.docker.internal` → `localhost` → `ollama:11434` → LAN scan on 11434 |
| Watcher notifications | `AI_ENRICH_BACKEND_URL` | configured URL → `backend:8000` → `host.docker.internal:8000` → `localhost:8000` |
| Scrapper logs | `SCRAPPER_LOG_BACKEND_URL` | when set to a non-loopback URL, batches are POSTed to that backend; unset/loopback keeps logs local |
| Dashboard health | `PROMETHEUS_URL`, `GRAFANA_URL` | those URLs (defaults point at `host.docker.internal`) |

The DB/Ollama scans are cached in `./data/discovery/cache.json`, which every service mounts, so containers starting together scan once instead of once each. Details: [commonlib service discovery](../apps/commonlib/README.md#service-discovery-mysql--mongodb--ollama), [agent docs](AGENTIC_SDLC.md#network-discovery) and each module README.

## Pinning a host (optional)

Discovery normally finds the service, so pin a host only when it lives on a subnet that is not swept, when a firewall blocks the scan, or when you want a deterministic target:

```bash
# .env — MySQL on another machine (host-native apps such as the scrapper)
COMMONLIB_DB_HOST=192.168.1.211

# .env — Ollama on another LAN machine (the AI workers can stay in Docker)
AI_ENRICH_OLLAMA_BASE_URL=http://192.168.1.211:11434
```

Compose pins the in-container DB/Mongo to the compose service names, and those `environment:` values outrank `.env`, so a `.env` pin applies to host-native apps (the scrapper) and to modules started outside Compose. To point a containerized service at a remote MySQL/Mongo, override its `environment:` in a compose override file.

`COMMONLIB_DISCOVERY_SUBNETS` (comma-separated CIDRs) adds subnets to the DB/Ollama sweep; `COMMONLIB_OLLAMA_DISCOVERY_SUBNETS` is the legacy Ollama-only alias. The Ollama sweep covers the container's own Docker subnet plus `192.168.0.0/24` and `192.168.1.0/24`, so a container reaches an Ollama on another PC in those ranges; `COMMONLIB_OLLAMA_DISCOVERY=False` disables the sweep.

### Scrapper logs on a remote backend

The [/statistics keyword chart](../apps/web/README.md) reads the scrapper's JSONL through the backend. When the scrapper runs on another machine that file stays there, so set `SCRAPPER_LOG_BACKEND_URL=http://<main-box-ip>:8000` on the scrapper box. The scrapper then batches its records to `POST /api/scrapper/logs` (every 5s or 200 records); the backend appends them to `SCRAPPER_LOG_DIR` (the Compose-mounted `apps/scrapper/data/logs`). Loopback URLs and an unset value keep the current local-only behaviour, so a single-machine install ships nothing. `SCRAPPER_LOG_BATCH_SIZE` and `SCRAPPER_LOG_FLUSH_SECONDS` tune the batching. Shipping is best-effort: a failed POST only logs a warning and retries with the next batch.

## Topologies

| Scenario | Setup |
|---|---|
| Everything on one machine (default) | `docker-compose up -d` |
| Scrapper on a separate machine | `COMMONLIB_DB_HOST=<mysql-host>` (or `auto`) in its `.env`, then `./apps/scrapper/run.sh`; add `SCRAPPER_LOG_BACKEND_URL=http://<main-box-ip>:8000` so its JSONL reaches the statistics chart |
| UI only on a client machine | run Vite natively there: `BACKEND_URL=http://<main-box-ip>:8000 ./apps/web/run.sh` (the `web` container is pinned to `backend:8000` by compose) |
| AI workers on another machine | run them natively there: `COMMONLIB_DB_HOST=<mysql-host> ./apps/aiEnrich/run.sh` (same for `aiEnrichSkill`), or keep them in Docker on the main box and point them at a LAN Ollama |

## Ollama: host, container or another LAN machine

The `ollama` service is **opt-in** (`--profile ollama`) and no module hard-depends on it, so it is never started implicitly. The Ollama-backed modules (`aienrich`, `aienrichskill`) resolve the server at startup: configured URL → `host.docker.internal` → `localhost` → `ollama:11434` → LAN scan. Before sending a job they run a one-token generation probe on the chosen server (`COMMONLIB_OLLAMA_PROBE_TIMEOUT`, default 30s) and remember a success for `COMMONLIB_OLLAMA_PROBE_CACHE_SECONDS` (default 300), so a wedged runner is skipped instead of blocking the job timeout and the following jobs go straight to inference.

```bash
# Ollama installed on the host, workers in Docker
docker-compose --profile aienrich up -d aienrich

# Ollama containerized as well
docker-compose --profile ollama --profile aienrich up -d

# Ollama on another LAN machine: set AI_ENRICH_OLLAMA_BASE_URL in .env, no Ollama service
docker-compose --profile aienrich --profile aiEnrichSkill up -d aienrich aienrichskill
```

For a remote Ollama, the server must listen beyond loopback (Ollama binds `127.0.0.1` by default) and the firewall must allow the port:

```bash
OLLAMA_HOST=0.0.0.0:11434 ollama serve

# verify from the Docker host or another LAN machine
curl http://192.168.1.211:11434/api/tags
```

The dashboard shows the resolved server (`ollama.serverIp` / `ollama.isLan`), and the worker healthchecks reuse the cached server, so a container running against a LAN Ollama reports healthy instead of being judged against the static fallbacks. Docker Desktop specifics (containerized Ollama is CPU-only, Windows firewall) are in [Docker Development](DOCKER_DEV.md#with-ai-services-ai-enrichment--ollama).
