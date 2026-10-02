# Normalize logging to structured logs across `apps/*`

Status: completed

Follow-up (after `da0a1842` dropped the human half of the records):

- `module` is now stamped from the calling app module by `observability.stamp_caller_module`
  (walk past `structlog`, `commonlib` and test-runner frames, stop at `__main__`); the
  `get_logger(name)` argument is only the fallback, and `module=` is rejected as a log
  field by the architecture test — a record carrying a stamped value uses `source_module`.
- `job_log_context(id)` binds `job_id` for the per-job work of aiEnrich, aiEnrich3,
  aiEnrichNew and aiCvMatcher, which also repairs the per-job duration gauge.
- `ai_helpers.footer()` is wired back with the batch elapsed time, and `ai_helpers.logIdleWait()`
  replaced the per-worker idle sleeps; the console renderer leads with `message`.

## Problem

Logging is inconsistent across the monorepo. Four AI modules (`aiEnrich`, `aiEnrich3`,
`aiEnrichNew`, `aiEnrichSkill`) already emit structured events through
`commonlib.observability` (structlog), with dotted `domain.action` event names and
`key=value` fields and no f-strings. Everything else still uses bare `print()`, often
wrapped in ANSI color helpers from `commonlib.terminalColor`.

| App | `print()` | structlog events | Status |
|---|---|---|---|
| scrapper | 219 (34 files) | 0 | none |
| commonlib | 82 (20 files) | ~30 (3 files) | split |
| cron | 16 (4 files) | 0 | none |
| aiCvMatcher | 13 | 0 | none, but the dashboard already reads its `app.jsonl`, which is never written |
| aiFormFiller | 10 | 0 | none |
| backend | 9 (+9 swallowed exceptions) | 0 | none |
| aiEnrich / 3 / New / Skill | 6 total | 76 | done |
| web | 45 `console.*` | n/a | browser SPA, out of scope |
| e2e | n/a | n/a | Playwright, out of scope |

## Target convention

```python
from commonlib.observability import configure_logging, get_logger

configure_logging("scrapper")
logger = get_logger("scrapper.executor")

logger.warning("job.retry", attempt=2, delay=3, base_url=url)
```

- Dotted `domain.action` event names, never free text.
- `key=value` fields, never f-strings in the log call.
- Levels: `debug` for per-item detail, `info` for lifecycle, `warning` for
  recoverable, `error` for failed operations, `exception` where a traceback matters.
- Presentational output (progress lines, tables, banners) stays `print`, but each
  phase is bracketed by structured events so the JSONL timeline is complete.

## Phases

### Phase 0 — Root causes in `commonlib/observability.py`

Two defects affect every app, so they land first.

1. **App-name race.** `get_logger()` calls `configure_logging()` with the default
   `app_name="app"`, and `commonlib/sql/query_executor.py:11` and
   `commonlib/ollama_client.py:18` build loggers at import time. Whichever import wins
   decides the JSONL file name, so every app ends up writing `app.jsonl` with
   `logger="app"`. Fix: an explicit `configure_logging("<app>")` from the entrypoint
   always wins and can re-point the writer after the fact; the file is named
   `<app>.jsonl`.
2. **Env var prefix.** `AI_ENRICH_LOG_DIR|LOG_LEVEL|LOG_COLOR|LOG_FILE_MAX_BYTES|LOG_FILE_BACKUP_COUNT`
   are read by apps that have nothing to do with aiEnrich. Rename to `LOG_*` with the
   `AI_ENRICH_*` names kept as fallback aliases so nothing breaks on restart. Resolve
   `LOG_DIR` at write time rather than import time.
3. Guard against creating `data/logs` under pytest.
4. Extend `commonlib/commonlib/test/observability_test.py`, split into a package to
   stay under the 200-line rule.

### Phase 1 — commonlib (20 files, 82 prints)

Highest leverage: every other app imports these modules.

- `environmentUtil.py:24,26,35` — module-level prints that fire on import of
  `commonlib` itself.
- `sync/mysql_sync.py` (12), `cv_loader.py` (11), `skill_enricher_service.py` (10),
  `ai_helpers.py` (7), `keep_system_awake.py` (5), `decorator/retry.py` (5),
  `terminalUtil.py` (4), `sql/transaction_manager.py` (4), `json_helpers.py` (4),
  `wake_timer.py` (3), `sql/connection_manager.py` (3), `network/mysql_discovery.py` (3),
  `terminalColor.py` (2), `stopWatch.py` (2), `sqlUtil.py` (1),
  `sql/query_executor.py` (1), `sql/mysqlUtil.py` (1), `exceptionUtil.py` (1).
- `terminalColor.printHR()` stays as-is: it is a rule-drawing primitive and its test
  asserts exact ANSI output.

Done: `environmentUtil.py`, `decorator/retry.py`, `terminalUtil.py`,
`network/mysql_discovery.py` (and previously `sync/mysql_sync.py`, `cv_loader.py`,
`skill_enricher_service.py`, `ai_helpers.py`, `keep_system_awake.py`,
`sql/transaction_manager.py`, `json_helpers.py`, `wake_timer.py`,
`sql/connection_manager.py`, `terminalColor.py`, `stopWatch.py`, `sqlUtil.py`,
`sql/query_executor.py`, `sql/mysqlUtil.py`, `exceptionUtil.py`).

Outcome notes for this batch:

- `environmentUtil.py` cannot import `commonlib.observability` at module scope
  (`observability` imports `environmentUtil`), and a module-level lazy import still
  runs while `observability` is only partially initialized. The events are therefore
  emitted through `_logEvent()`, which imports `observability` lazily at call time:
  `env.loaded` (debug) fires once on the first `getEnv()`/`checkEnvReload()` and
  `env.reloaded` (info) fires when the dotenv files change. Only file paths are
  logged, never values.
- `checkEnvReload()` reenters itself through `get_logger` → `configure_logging` →
  `getEnv`, so a `_envReloading` reentrancy guard wraps the reload and its event.
  The reload now commits `envLastModified` before logging so nested reads see the
  new environment.
- `decorator/retry.py` keeps all five prints (progress chain plus the
  `stackTrace`-gated tracebacks) and adds `retry.attempt` (warning) and
  `retry.exhausted` (error). `logger.exception` is deliberately not used there:
  `stackTrace=StackTrace.NEVER` must keep suppressing tracebacks.
- `terminalUtil.py` keeps the in-place countdown output as `print` and brackets it
  with `timer.requested` (debug), `timer.started` and `timer.completed` (info).

### Phase 2 — cron (4 files, 16 prints)

`configure_logging("cron")` first line of `run()`. `scheduler.py:54` red `FAILED` print
becomes `cron.job_failed` via `logger.exception`. Coverage gate `fail_under = 85`.

### Phase 3 — aiCvMatcher (13) + aiFormFiller (10)

- aiCvMatcher gets the JSONL its already-mounted volume and the dashboard's
  `LOG_SOURCES` entry expect. `cvMatcher_test.py` patches `print` / `yellow` / `red`
  and must be rewritten to patch the logger.
- aiFormFiller swallows provider errors into `HTTPException` with no record; add
  `provider.failed`. Add a `data/logs` mount for parity, but no dashboard entry —
  it is an interactive service, not a batch job.

Done.

Outcome notes for this batch:

- The 13 aiCvMatcher and 10 aiFormFiller prints are converted; the only surviving
  `print` is the `consoleTimer(...)` countdown in `aiCvMatcher/main.py`, which
  redraws in place with `end='\r'`, so `terminalColor.cyan` stays imported there.
- `aiCvMatcher/main.py` calls `configure_logging("aiCvMatcher")` as the first
  statement of `run()`, and `aiFormFiller/main.py` calls it at module level after
  the imports and before `app = create_app()`, because that call happens at import
  time and its `app.created` / `app.context_loaded` events must be attributed to
  the app rather than to the provisional `app` name.
- `cvMatcher_test.py` no longer patches `print`/`yellow`/`red`. A `patched_matcher`
  context manager replaces the repeated `SentenceTransformer` / `CVLoader` /
  `getEnvBool` stacks, and the log assertions patch `aiCvMatcher.cvMatcher.logger`
  directly, so the same assertions are made against event name and fields. The
  `test_footer_err` case became the parameterized `test_footer_logs_summary`, which
  also pins the no-error path (`log.warning.assert_not_called`).
- `apps/aiCvMatcher/src/aiCvMatcher/test/main_test.py` and
  `apps/aiFormFiller/src/aiFormFiller/test/main_test.py` use
  `structlog.testing.capture_logs()` to assert the entrypoint events and, in the
  aiFormFiller case, that `app.context_loaded` carries only the two booleans — a
  regression guard against CV content leaking into a log field.
- `dashboard_repository.LOG_SOURCES` was pointing every module at `app.jsonl`, but
  `configure_logging("<app>")` names the file after the app, so the dashboard was
  reading a stale file for all five modules and would have read nothing at all for
  aiCvMatcher. `LOG_SOURCES` now holds the per-app path and `resolve_log_path()`
  falls back to `app.jsonl`, which keeps the pre-existing history rendering. Done
  as part of this phase rather than Phase 6, because it is the reason this phase
  exists.

### Phase 4 — backend (9 prints + 9 swallowed exceptions)

`configure_logging("backend")` must run before any repository module builds a logger,
so it goes in a `logging_setup.py` imported first by `api/main.py` and `main.py`.
Convert the 9 `print(red(...))` exception sites and add `logger.debug` to the 12
silent `except` blocks. `repository_utils.py:19` interpolates SQL and bind params
today; as structured fields the param values must stay out. Add a request-logging
middleware so the JSONL contains the request timeline, not just uvicorn's stdout.

### Phase 5 — scrapper (34 files, 219 prints)

Leverage first: `printScrapperTitle` has 1 call site, `printPage` and `summarize` have
6 each, so rewriting the three functions in `core/baseScrapper.py` retires ~13 call
sites. Split `core/utils.py:debug()` into a logger call plus a separate interactive
pause. `core/scrapper_config.py:31` prints the whole config dict at import. The status
table and failed-information table stay presentational. Then breadth, file by file,
f-string to `key=value`. Coverage gate `fail_under = 85`.

### Phase 6 — Infrastructure

- `scripts/test-sandbox.sh:114` and `.bat:114` gate on
  `grep -E 'ERROR|CRITICAL|Traceback'`, but structlog emits lowercase
  `error`/`critical`. Make the gate case-insensitive.
- `backend/repositories/dashboard_repository.py` `LOG_SOURCES` now holds the per-app
  path with an `app.jsonl` fallback so existing history keeps rendering. Done in
  Phase 3.
- `docker-compose.yml` gains log mounts for aiFormFiller, scrapper and cron.

Done.

Outcome notes for this batch:

- `scripts/test-sandbox.sh` gate is now `grep -iE 'ERROR|CRITICAL|Traceback'`; the
  `.bat` gate already used `findstr /i`.
- `docker-compose.yml` `backend` gains read-only collector mounts
  `./apps/scrapper/data/logs:/logs/scrapper:ro`,
  `./apps/cron/data/logs:/logs/cron:ro` and
  `./apps/aiFormFiller/data/logs:/logs/aiformfiller:ro`, matching the existing
  `/logs/aienrich|aienrich3|aienrichnew|aienrichskill|aicvmatcher` mounts. Each
  app's `Dockerfile` ends on `WORKDIR /app/apps/<App>` and `LOG_DIR` defaults to
  `data/logs`, so `apps/<App>/data/logs/<app>.jsonl` on the host is shared from
  both sides. `docker-compose config` validates.

### Phase 7 — Consistency pass and regression guard

Remove the duplicate `print(cyan(...))` version banners next to existing
`logger.info("startup", ...)` calls in the four migrated apps, convert their remaining
`traceback.print_exc()` calls, and add a commonlib architecture test asserting no
`print(` in `apps/*` outside a small allowlist of presentational helpers.

Done.

Outcome notes for this batch:

- Duplicate `print(cyan(f"... v{_v(...)}"))` banners removed from `aiEnrich`,
  `aiEnrich3`, `aiEnrichNew` and `aiEnrichSkill` `main.py`; the structured
  `startup` event already carries `version=`. The now-unused `cyan` import was
  dropped from `aiEnrich/main.py` only; the other three still use it for their
  retry/countdown spinners.
- `traceback.print_exc()` / `traceback.format_exc()` passed to `logger.error(...)`
  converted to `logger.exception(...)` in `aiEnrich/dataExtractor.py`,
  `aiEnrich3/services/job_enrichment_service.py`, `aiEnrichNew/llm_utils.py`,
  `aiEnrichNew/services/job_enrichment_service.py`, `aiEnrichSkill/llm_utils.py`;
  the `import traceback` lines are gone from each. All call sites run inside a live
  `except` block, so `logger.exception` captures the active traceback.
- New `apps/commonlib/commonlib/test/architecture/architecture_logging.py`:
  AST-scan driven `get_print_violations()` over `apps/*` (skips venvs, tests) with a
  `PRINT_ALLOWLIST` of the 21 files whose `print()` output is genuinely
  presentational (tables, spinners, prompts, `printHR`, gated retry tracebacks).
  Wired as `test_no_bare_print_in_source()` in `architecture_test.py`.

### Phase 8 — Tests and docs

`.\scripts\test.bat commonlib cron aiCvMatcher aiFormFiller backend scrapper` after each
phase, then the sandbox gate for `cron`, `backend` and `aiformfiller`. Docs to update
per the documentation-sync rule: root `README.md` (Settings, Docker Compose volumes),
`AGENTS.md`, `.claude/CLAUDE.md`, `READMEs/README_METRICS.md`, `READMEs/DOCKER_DEV.md`,
`READMZs/TODO.md`, and the per-app READMEs. Then `scripts\graphify\graphify.bat update .`.

Done.

Outcome notes for this batch:

- `.\scripts\test.bat commonlib cron scrapper backend aiCvMatcher aiFormFiller
  aiEnrich aiEnrich3 aiEnrichNew aiEnrichSkill` is green: 703 + 33 + 564 + 487 +
  17 + 79 + 106 + 56 + 34 + 53 = 2132 tests.
- Scrapper conversions surfaced three regressions that are now fixed: the
  `browserService` module/`browser_service` fixture name collision
  (`from scrapper.services.selenium import browser_service as browser_service_mod`
  in `browser_service_test.py`); the agent's log-only rewrite changed
  `waitUntil_presenceLocatedElement_noError` casing and duplicated an
  `ignore_access_key_form()` call in `indeedAuthenticator.py` (both reverted to
  match the original behavior); `driverUtil_test.py` is no longer coupled to the
  real `.env` (`SCRAPPER_USE_UNDETECTED_CHROMEDRIVER` patched False) and declares
  `uc.Chrome` expected for both windows and posix (the code calls it in both
  branches).
- Structured-logging docs moved to `READMEs/README_DEVELOPMENT.md#structured-logging`
  (root `README.md` keeps pointers); backend `/metrics` `KeyError` from
  aiEnrichSkill's `job.result` events fixed by renaming them to `skill.result` and
  hardening `prometheus_exporter.build_log_metrics`. `AGENTS.md` Code Style now
  documents the `PRINT_ALLOWLIST` architecture test. `graphify-out/` refreshed.

## Risks

- Six stdout-asserting scrapper tests and two `cvMatcher` tests are coupled to `print`
  and must be rewritten rather than removed, to hold the 85% coverage gates.
- `repository_utils.py:19` currently logs SQL and params; structured fields make it
  easier to leak credentials, so param values stay out.
- The dashboard's `app.jsonl` paths need the fallback or existing history disappears
  from the UI.
