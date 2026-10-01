# AI Job Search Default Development Guide

This guide covers setting up your development environment, running the application manually, and testing.

## Development with VS Code

To ensure VS Code automatically selects the correct interpreter for each project:

1. **Open the Workspace**: Open the `.vscode/AI-job-search.code-workspace` file in VS Code (`File > Open Workspace from File...`).
2. **Interpreter Selection**: The workspace is configured to automatically pick up the `.venv` in each application folder (`apps/backend`, `apps/scrapper`, etc.).

> **Note the root `pyproject.toml` is not required** for deploying or running the applications**, as each module (in `apps/`) has its own dependencies and configuration for Docker and CI/CD. However, it is **highly necessary for the local Developer Experience (DX)**. It configures the virtual environment used by the VS Code Workspace (`.venv`), providing global linting/formatting tools (like `black`, `ruff`, and `mypy`), and ensures the IDE can correctly resolve cross-module imports like `commonlib`.



## Testing

Run all tests across the monorepo:

- **Linux**: `./scripts/test.sh` (Optional: `--coverage`)
- **Windows**: `.\scripts\test.bat` (Optional: `--coverage`)

Run specific app tests (single or multiple):

- **Linux**: `./scripts/test.sh commonlib` or `./scripts/test.sh commonlib web e2e`
- **Windows**: `.\scripts\test.bat commonlib` or `.\scripts\test.bat commonlib web e2e`

### When to run the suites

Run them when the change touches **test code, production code, or the test runner
scripts** (`scripts/test.sh`, `scripts/test.bat`) — always include `commonlib`, and every
other modified `apps/*` module.

Skip them when the change is limited to **documentation or non-test scripts/config**: CI
workflows, coverage gates, install/sandbox helpers, agent rules and skills. Those files are
not exercised by the unit or e2e suites, so a run proves nothing; say so in the summary
instead.

## Coverage Gates

`--coverage` does not only produce reports and badges: it enforces two floors on
**statements and lines only** (functions and branches are reported, never gated).
The coverage floor is 90% for the web frontend and for the scrapper.

### Frontend: web unit + e2e union

`scripts/coverage/frontend-coverage-gate.mjs` gates the **union** of the two frontend
suites, because neither number alone is meaningful: a lazily-routed page is invisible
to the unit run and barely touched by e2e.

```bash
# Both reports must exist; both suites include every production file under apps/web/src
(cd apps/web && npm test -- run --coverage)
(cd apps/e2e && npm test)
node scripts/coverage/frontend-coverage-gate.mjs --min 90
```

- Per file, `total` and `covered` are the max of the two reports. Both tools count the
  same source lines, so max is the standard approximation for a union of covered-line
  sets (an exact union is not derivable from counts alone, since the two suites may
  cover the same line).
- There is deliberately **no separate e2e floor**: the e2e badge shows the union.
- Vitest keys are absolute and monocart keys are entry-URL relative (`src/...`); the
  gate canonicalises both to `apps/web/src/...` and **fails on denominator drift**, i.e.
  when the two suites did not measure the same file set.
- Test files, CSS and `node_modules` are excluded from both feeds, so the denominator
  is production code only.
- Outputs the merged report to `apps/e2e/coverage/coverage-frontend-summary.json`.

### Scrapper: production statements

```bash
cd apps/scrapper
poetry run coverage run -m pytest
poetry run coverage xml
python ../../scripts/coverage/scrapper_coverage_gate.py --min 90
```

Tests live inside the package, so `[tool.coverage.run] omit` keeps `*/test/*` and
`*/conftest.py` out of the denominator — without it, near-perfectly covered test files
inflated the badge by ~8.8 points. `fail_under` is intentionally **not** set: coverage.py
only compares the branch-inclusive total, which this project does not gate on.

## Structured Logging

Every Python app in `apps/*` logs through one shared `structlog` configuration in `commonlib.observability`. Records are JSON lines with a dotted `domain.action` event name and `key=value` fields, written to stdout *and* mirrored to a per-app JSONL file. The backend dashboard and the Prometheus exporter in `commonlib.prometheus_exporter` read those files, so keeping the event names and fields stable is a contract, not a style preference.

### Wiring an app

The entrypoint configures logging as its first executable statement, before any other module logs:

```python
from commonlib.observability import configure_logging, get_logger


def run():
    configure_logging("myApp")
    logger = get_logger("myApp.main")
    logger.info("app.started")
```

The order matters. `LOG_LEVEL` and `LOG_COLOR` are read once, when structlog is first configured, and frozen on each logger's first call. The app *name* is resolved per record, so a later `configure_logging()` still re-points the JSONL file; the level cannot change that late.

`get_logger(name)` binds `name` to the `module` field explicitly, because `structlog.get_logger(name)` hands the name to the logger factory and `PrintLoggerFactory` discards it.

### Conventions

| Rule | Example |
|---|---|
| Event names are dotted `domain.action`, never sentences | `logger.info("job.result", job_id=id, duration=1.5)` |
| No f-strings in log calls; every dynamic value is a field | `logger.warning("job.retry", attempt=2, delay=3)` — not `f"retry {n}"` |
| Levels: `debug` per-item detail, `info` lifecycle, `warning` recoverable, `error` failed operation |  |
| Inside `except`, use `logger.exception(...)`; never pass `traceback=` | `logger.exception("skill.failed", skill=name, error=str(ex))` |
| Never log secrets, env values, SQL bind values, CV text, or model prompts/answers | log lengths, ids, names, counts, durations instead |
| Never log whole documents or large blobs | pass ids and counts as fields |

Records carry `event`, `module` (the `get_logger` name), `logger` (the app name), `level`, and an ISO `timestamp`, plus whatever fields the call site passes.

**Progress bars, countdowns, tables, and banners stay `print`.** They are presentational output that a person reads in a terminal, not signals to scrape. Anything using `end=`, `flush=True`, or `\r` for in-place updates stays as `print`; wrap those phases in structured lifecycle events (`job.started` / `job.completed`) so the sequence is still observable. Colors from `commonlib.terminalColor` are only for these presentational prints — drop the import when the last colored print goes.

The in-place redraw only applies on an interactive terminal. When the helper runs in a container (`commonlib.terminalUtil.consoleTimerDocker`, i.e. `isDocker()`), the static countdown line is skipped and the wait is collapsed to a single `timer.started` record (no `timer.completed`): `docker-compose logs` is not an interactive console, so one line per idle cycle is enough. ANSI escape codes passed into the helpers are stripped before a `message` lands in a record.

### Two console modes

A record can carry two halves: the structured fields the JSONL stores, and the human line a person reads. The `console` field holds the human line, so an app can keep its old console wording without giving up queryable records:

```python
logger.info("linkedin.job.processed", job_id=job_id, insert_id=id,
            console=green(f"{job_id}, {title}, {cyan(company)} - "), end="")
```

| Mode | Console | File |
|---|---|---|
| `CONSOLE_RECORD` (default) | the `console=` text if present, otherwise the rendered record | every record |
| `CONSOLE_MESSAGE` | the `console=` text only, with no timestamp, level, or event name | every record |

`CONSOLE_MESSAGE` is how an app keeps a quiet, old-style console: a record without `console=` is written to the JSONL and never reaches stdout, which also mutes the chatter of the shared `commonlib` modules the app imports. The scrapper is the reference implementation (`apps/scrapper/README.md`).

| Field | Effect |
|---|---|
| `console=` | The text to print. Anything non-string is coerced; the raw text (colors included) never reaches the file, only the ANSI-stripped `message` |
| `end=` | Terminator for the console text, `"\n"` by default. `end=""` rebuilds a `print(..., end='')` progress prefix. It is ignored in `CONSOLE_RECORD` mode, which always ends the rendered record with a newline, and it never reaches the file |

The mode is resolved per record instead of when structlog is configured, so an entrypoint can select it after a shared module already logged (`commonlib.sql.query_executor` and `commonlib.ollama_client` build their loggers at import time). An entrypoint selects it with `configure_logging("<app>", console=CONSOLE_MESSAGE)`.

Two rules follow from the split:

- A record that prints something a person needed before `LOG_LEVEL=20` became the default is logged at `info`, even if the wording says "DEBUG". Keep the level meaningful, not the old severity.
- The console text is still a log line, so it obeys the same rules: no secrets, no blobs, and no query strings that carry tracking parameters.

### Configuration

All apps share these variables. They can be set in `.env` (bind-mounted into every container, so a restart is enough — no rebuild) or per service in `docker-compose.yml`.

| Variable | Default | Meaning |
|---|---|---|
| `LOG_LEVEL` | `20` | 10=DEBUG, 20=INFO, 30=WARNING, 40=ERROR |
| `LOG_COLOR` | `True` | Colored console output instead of raw JSON on stdout |
| `LOG_CONSOLE_MODE` | `record` | `record` renders each record, `message` prints only the `console=` text |
| `LOG_DIR` | `data/logs` | Directory holding the JSONL files |
| `LOG_APP_NAME` | `app` | Provisional app name, used until an entrypoint sets one |
| `LOG_FILE_MAX_BYTES` | `10485760` | Rotate the file once it grows past this |
| `LOG_FILE_BACKUP_COUNT` | `5` | Rotated files to keep (`<app>.jsonl.1` … `.N`) |

`AI_ENRICH_LOG_*` names predate the modules that share this library and are still read as deprecated aliases; prefer the generic names for new configuration. `LOG_CONSOLE_MODE` is what an entrypoint passes as `console=` to `configure_logging`; an app such as the scrapper hard-codes its mode and only reads the variable when no entrypoint has selected one.

### Output layout

Each app writes `data/logs/<app>.jsonl` relative to its working directory — for example `apps/cron/data/logs/cron.jsonl` on the host. The directory is created on first write, and file I/O failures are swallowed deliberately: losing a log line must never take down a worker. Containers receive the same files through the read-only log mounts declared in `docker-compose.yml`.

```bash
# Tail one app
tail -f apps/backend/data/logs/backend.jsonl

# Count events by level
jq -r '.level' apps/backend/data/logs/backend.jsonl | sort | uniq -c

# Top event names
jq -r '.event' apps/backend/data/logs/backend.jsonl | sort | uniq -c | sort -rn | head
```

Per-app details live in each module's own README (`apps/<module>/README.md`); the metrics contract built on top of these files is in [README_METRICS.md](README_METRICS.md).

## Agentic SDLC

Agent skills, rules, and workflows (including graphify and the dependabot agent) are documented in [AGENTIC_SDLC.md](AGENTIC_SDLC.md). All agent skills live under `.claude/skills/`.

## Documentation Sync

Documentation is part of the implementation: after every plan implementation, feature, fix, or config change, the affected docs are updated in the same session. The change → docs map and the definition-of-done checklist live in `.claude/rules/documentation-update.md` and are described in [AGENTIC_SDLC.md](AGENTIC_SDLC.md#documentation-sync-automatic-mandatory).

## Related Documentation

- **Agentic SDLC**: [AGENTIC_SDLC.md](AGENTIC_SDLC.md)
- **Installation Guide**: [README_INSTALL.md](README_INSTALL.md)
- **Docker Development**: [DOCKER_DEV.md](DOCKER_DEV.md)
- **Contribution Guide**: [README_CONTRIBUTE.md](README_CONTRIBUTE.md)
- **Metrics & Grafana**: [README_METRICS.md](README_METRICS.md)
