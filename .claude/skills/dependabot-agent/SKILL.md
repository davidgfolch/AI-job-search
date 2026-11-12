---
name: dependabot-agent
description: Sync staging from master first, then process open GitHub Dependabot PRs inside a throwaway sibling clone (../ai_job_search-dependabot-<pr>, created with scripts/dev.sh dep) so the main working tree is never touched: check the library changelog for breaking changes, make required changes and build, run all tests, sandbox-build AND run the affected docker-compose services, verify the logs are error-free, confirm the GitHub pipeline completes, then merge and delete the clone. Any sandbox error aborts the process. Requires the GitHub CLI (gh). Master is never pushed to directly — the persistent staging→master PR handles promotion.
---

# Dependabot Agent Instructions

This skill automates the handling of Dependabot PRs in this monorepo. Every PR is handled in its own throwaway sibling clone (`../ai_job_search-dependabot-<pr>`) created with the shared dev workflow (`scripts/dev.sh`, or `scripts/dev.bat` on Windows) — the same per-feature clone flow `../rag-systems` uses with `scripts/dev.*` (`new` → work → `merge` → delete the clone). While a PR is being handled the main workspace, its branches, its lockfiles and its running stack are never touched. Dependabot opens PRs against the `staging` branch (see `.github/dependabot.yml`), grouping minor/patch updates per ecosystem. A workflow (`.github/workflows/dependabot-auto-merge.yml`) auto-merges grouped `minor-patch`/`github-actions` PRs once CI is green, but it **skips semver-major PRs** and any PR whose CI fails. This agent acts where automation cannot: it does the changelog sanity check, runs the module tests locally, builds the affected docker-compose services, verifies the logs, fixes failures, and pushes to the PR branch so auto-merge can proceed. It never pushes to `master`.

## Prerequisites

- GitHub CLI installed and authenticated: `gh auth status`.
- Local env ready: `docker-compose up -d` (MySQL) and `.env.secrets` present in the main workspace (copy `scripts/.env.secrets.example` if missing — **never commit it**).
- The main workspace does **not** need a clean tree: step 0 fast-forwards `staging` there (branch move only, no file edits), and every other step runs in the sibling clone.
- Only one sandbox at a time: `scripts/test-sandbox.*` always uses the fixed compose project `dependabot-test` with remapped ports, so never run a sandbox from the main checkout while the clone's sandbox is up.

## Isolated workspace (sibling clone)

One clone per PR, always a sibling of the project root and always prefixed `ai_job_search-`:

```
<parent>/ai_job_search                      # main workspace — no file edits while a PR is handled
<parent>/ai_job_search-dependabot-276       # clone for PR #276
```

```bash
# From the main workspace (or any workspace copy): creates ../ai_job_search-dependabot-<n>,
# runs `gh pr checkout <n>` (branch + upstream tracking), and copies the gitignored runtime
# state the pipeline needs: .env, .env.secrets and apps/*/{uv,poetry}.lock, package-lock.json.
# scripts/test.sh picks uv vs poetry by lockfile presence, so the lockfiles matter.
./scripts/dev.sh dep <n>
cd "$(dirname "$(git rev-parse --show-toplevel)")/ai_job_search-dependabot-<n>"

# Windows
.\scripts\dev.bat dep <n>
```

- Every command of the pipeline (tests, sandbox, commit, push) runs **with the clone as working directory**; `scripts/test.sh` and `scripts/test-sandbox.sh` resolve their modules, `.env` and `.docker-sandbox/` from their own location, so they operate on the clone.
- Nothing is ever committed from the main workspace, and `.env.secrets` is never staged (it is gitignored in the clone too).
- `./scripts/dev.sh list` shows the sibling clones; `./scripts/dev.sh status` prints branch, dirty state and ahead/behind.

## Workflow

### 0. Sync `staging` from `master` — always, before any other Dependabot action

Dependabot PRs branch off `staging`, so a `staging` that is behind `master` makes every PR (and its CI) run against a stale base and drifts the `staging → master` promotion PR. Run this once per batch, before listing or processing anything:

```bash
./scripts/dev.sh sync        # Windows: .\scripts\dev.bat sync
```

- `sync` fetches, checks out `staging`, pulls it, fast-forwards it to `master`, and pushes only when it actually advanced.
- Fast-forward only. If `staging` and `master` diverged (hotfix on `master`, promotion mid-flight), it stops and reports instead of creating a merge commit — resolve that manually before continuing.
- `staging` ahead of `master` is the normal pending-promotion state: the merge is a no-op and nothing is pushed.

### 1. List open Dependabot PRs

```bash
gh pr list --app dependabot --state open --json number,title,headRefName,baseRefName,isDraft
```

- Process PRs where `baseRefName == "staging"`.
- Any PR still targeting `master` is legacy (config was retargeted to staging). Close it with a comment; Dependabot recreates it against staging on its next run:
  ```bash
  gh pr close <n> --comment "Obsolete: now targets the staging branch (dependabot-agent)."
  ```

### 2. Process each PR (smallest PR number first)

For each open staging PR:

1. **Detect affected modules**:
   ```bash
   gh pr diff <n> --name-only
   ```
   Map paths under `apps/<name>/**` to the module name (`apps/web` → `web`, `apps/backend` → `backend`, etc.). A `commonlib` bump means all Python dependents must be tested (matches the `ci.yml` matrix logic). Only modules touched by the diff are affected; if only `.github/**` or lockfiles changed, the affected set is empty but still validate the pipeline.

2. **Determine the semver level**: read the PR body/title for the `version-update:semver-(major|minor|patch)` tag. Grouped minor/patch PRs are auto-merge eligible; semver-major and ungrouped PRs are not.

3. **Create the isolated clone and check out the PR branch**:
   ```bash
   ./scripts/dev.sh dep <n>        # Windows: .\scripts\dev.bat dep <n>
   ```
   That creates/repopulates `../ai_job_search-dependabot-<n>`, copies the gitignored env + lockfiles, and leaves the PR branch checked out with its upstream set. From here on, every command runs inside that clone.

### 3. Changelog / breaking-change gate

- For **auto-merge-eligible PRs** (grouped minor/patch), trust the grouping; no changelog review is required before proceeding.
- For **semver-major or ungrouped PRs**, check the new library's release notes/changelog (e.g. `gh api repos/<owner>/<repo>/releases` or the upstream changelog) for breaking/API changes relevant to how the module uses the library.
  - If it introduces breaking changes requiring non-trivial migration:
    ```bash
    gh pr comment <n> --body "Changelog review: this release has breaking changes (<summary>). Flagging for human review before code changes."
    ```
    and leave the PR open.
  - Otherwise continue with the build/test pipeline.

### 4. Run the TDD pipeline for the module

This regenerates lockfiles/badges like CI does (`ci.yml` runs this matrix):
```bash
# From the clone root.
# Windows
.\scripts\test.bat <module>
# Linux/Mac
./scripts/test.sh <module>
# Or via the dev workflow, which delegates to the same runner in this clone:
./scripts/dev.sh test <module>
```
For a `commonlib` bump run the full Python dependent set, e.g. `./scripts/test.sh commonlib backend scrapper aiEnrich aiEnrichSkill aiCvMatcher aiFormFiller cron`.

Run it from the clone root — never from the main workspace — so the generated lockfiles/badges belong to the PR branch. The install step also regenerates the clone's gitignored lockfiles, which is why they were copied in first.

### 5. Sandbox build+run the affected docker-compose services and check logs — MANDATORY GATE

Every PR whose diff touchs a module that runs in the compose stack **must** be built **and** run in the isolated sandbox, and the logs must be clean. The sandbox uses `docker-compose.test.override.yml` (renamed `-test` containers, ports `!override` so no host port collides with the live stack, data isolated under `.docker-sandbox/`). The scripts handle build, MySQL clone, log check, and teardown:

```bash
# From the clone root.
# Windows
.\scripts\test-sandbox.bat <service>
# Linux/Mac
./scripts/test-sandbox.sh <service>
```

The sandbox always runs under the fixed compose project `dependabot-test` with remapped ports and a clone-local `.docker-sandbox/`, so it is isolated from the live stack but **not** from a second simultaneous sandbox: make sure no other `test-sandbox.*` run is active before starting one.

- Use the affected composed service name, e.g. `backend` or `web`. The script brings up only that service plus its DB dependencies in the isolated `dependabot-test` project. The `aiEnrich*` workers except `aienrich`/`aienrichskill`, plus `aicvmatcher`, `cron`, and `aiformfiller`, are sandbox-runnable; the profile-gated ones need their profile, e.g. `.\scripts\test-sandbox.bat --profile aiEnrichSkill aienrichskill`.
- **Deterministic addresses — no autodiscovery**: the sandbox never autodiscovers IPs/ports. `docker-compose.test.override.yml` pins every interacting URL to the sandbox service names + internal ports (e.g. web `BACKEND_URL=http://backend:8000`, backend `COMMONLIB_DB_HOST=mysql_db` + `MONGO_URI=...mongo_db:27017`), and sets `COMMONLIB_DB_DISCOVERY=False` so commonlib never LAN-scans for MySQL (which would otherwise find the LIVE mysql at the docker bridge). Services NOT deployed in the sandbox point to the host (`host.docker.internal`, e.g. ollama at `:11434`). The web dev-proxy skips its probe/scan because `BACKEND_URL` is set.
- **Disabled aiEnrich modules are build-only**: the script reads the module enable flags from `.env` (`AI_ENRICH_JOB`/`AI_ENRICH_SKILL`, `AI_ENRICHSKILL_ENABLED`, `AI_CVMATCHER_ENABLED`). If every flag for the module is false, it does a **build-only** check and does not require the service to run/process.
- **MySQL data clone**: the script dumps the live `jobs` DB (`scripts/mysql/backup.*`) into `scripts/mysql/backups/`, then restores it into the sandbox mysql container. Skip with `--no-db-clone`. The sandbox mysql is initialized only from the schema SQL files (`ddl.sql`, `skills_data.sql`), never from the maintenance `backup.*`/`restore.*` scripts (they break the MySQL entrypoint on fresh boots due to CRLF) nor the scratch `mysql_queries.sql` (it has a SQL syntax error). The override uses a strict authenticated TCP healthcheck and the script waits for `SELECT 1` before restoring, so the clone never races the mysqld entrypoint restart.
- **Mongo**: the sandbox spins a fresh, empty Mongo seeded by `scripts/mongo/init.js` (full isolation) — the base full-stack Mongo is never touched.
- **Ollama/prometheus/grafana are never duplicated**: they are not defined in the override.
- **Ollama-dependent services** (`aienrich`, `aienrichskill`, `scrapper`): no longer hard-depend on the `ollama` service (it is opt-in via `--profile ollama`), but they are still validated **build-only** in the sandbox because the sandbox does not provide a reachable Ollama for them to do real work against. Do a **build-only** check (which still must succeed):
  ```bash
  docker compose -f docker-compose.yml -f docker-compose.test.override.yml -p dependabot-test build <service>
  ```
  Then tear the build artifacts down.
- **Check for startup success and errors** in the sandbox:
  ```bash
  docker compose -p dependabot-test ps                 # sandbox services should be Up (healthy)
  docker compose -p dependabot-test logs <service> --tail=100
  ```
  The log check must show **zero ERROR/CRITICAL/Traceback lines** and no restart loops, non-zero exits, or failed healthchecks. The `test-sandbox.*` scripts perform this scan **automatically** and exit non-zero on failure, so treat a non-zero exit as an abort signal without further log reading.
- **A sandbox error ABORTS the dependabot process**: if the build fails, a service fails to start, or the logs contain errors, STOP — do not merge, do not move on to the next PR. Fix the underlying cause (the sandbox fix may itself be a required change) and re-run the sandbox until it is clean. Do not treat known build errors as "pre-existing and acceptable".
- **Skip ONLY** for a module that never runs in the compose stack (e.g. pure `apps/e2e` only).
- The wrapper tears down the sandbox (removes containers, the `mongo_data_sandbox` volume, and the `.docker-sandbox/` dir) on exit unless `--keep` is passed.

### 6. Green result

- Regenerate/commit any lockfile/badge churn the test run produced inside the clone (e.g. `poetry.lock`, `uv.lock`, `package-lock.json`):
  ```bash
  git add -A && git commit -m "chore: regenerate lockfile for <module>" && git push
  ```
  `./scripts/dev.sh commit "..."` / `./scripts/dev.sh push` are the equivalents once the clone has the dev workflow. `gh pr checkout` set the upstream, so the push updates the PR head branch; never force-push.
- **Check GitHub pipeline completion** — this is the acceptance gate. Wait for CI and confirm the final `ci-gate` job (from `ci.yml`) passes:
  ```bash
  gh pr checks <n> --watch
  ```
  Only treat the PR as green when the run is complete and `ci-gate` succeeded (and docker/log checks above passed).
- For auto-merge-eligible PRs, verify merge is enabled — the merge to staging happens automatically once checks pass:
  ```bash
  gh pr view <n> --json state,mergeStateStatus
  ```
- For PRs that are not auto-merge eligible (semver-major guard, or ungrouped PR reviewed by a human), merge explicitly only when checks and `ci-gate` are green:
  ```bash
  gh pr merge <n> --squash
  ```
- Post a short summary comment on the PR documenting what changed and that docker/log/pipeline checks passed.

### 7. Red result

- Read the failure output. Common causes: API/code breaking changes in a new version, a too-narrow dependency constraint, or lockfile churn.
- Fix only what is required to make the module green: bump constraints in the module's `pyproject.toml`/`package.json`, or patch code/tests for the new version.
- Re-run the module tests via the centralized script (`.\scripts\test.bat commonlib <module>` or `./scripts/test.sh commonlib <module>`), which also runs architecture checks:
  ```bash
  # Linux/Mac
  ./scripts/test.sh commonlib <module>
  # Windows
  .\scripts\test.bat commonlib <module>
  ```
- Re-run step 5 (sandbox build + logs via `scripts/test-sandbox.*`) after a code/constraint fix if the affected service is a composed one.
- Commit + push and re-verify until green.
- If the failure cannot be fixed within reasonable effort, post the diagnosis and leave the PR open:
  ```bash
  gh pr comment <n> --body "<root cause and what was tried>"
  ```

### 8. Wrap-up

- **Delete the sibling clone** once the PR is safely merged (or on an explicit request to discard it):
  ```bash
  ./scripts/dev.sh cleanup dependabot-<n>      # Windows: .\scripts\dev.bat cleanup dependabot-<n>
  ```
  `cleanup` refuses anything that is not a sibling directory named `ai_job_search-*` holding a git work tree, so it cannot remove the main workspace. If the delete fails (Windows editor/CodeGraph daemon holding files), stop the clone's CodeGraph daemon and retry once. On a red result keep the clone for inspection and report its path instead of deleting it.
- Back in the **main workspace**, refresh `staging` again to pick up the PR's own merge (step 0 already left the workspace on `staging`). Apart from the step-0 sync this is the only main-workspace action — no file edits or commits there:
  ```bash
  git -C "$(git rev-parse --show-toplevel)" pull --ff-only origin staging
  ```
- Verify the persistent `staging → master` PR is healthy (promotion is automatic via auto-merge). It closes on each merge, so if none is open and `staging` is ahead of `master`, recreate it (with gh on PATH):
  ```bash
  gh pr list --base master --head staging --json number,state --jq '.[0].number'
  gh pr create --base master --head staging --title "chore: promote staging to master" --body "Auto-generated persistent promotion PR from the staging gate. Auto-merge enabled."
  gh pr merge <new-pr-number> --auto --squash
  ```
  If `staging` and `master` have identical content the PR cannot be created yet — wait for the next Dependabot merge into `staging`, then recreate.

## Safety rules

- Never push to `master` directly and never force-push.
- Only ever delete sibling directories named `ai_job_search-*` that are git clones sitting next to the main workspace (that is what `./scripts/dev.sh cleanup` enforces); never delete, reset or check out branches in the main workspace.
- Never commit `.env.secrets` or any credentials.
- Only change code required to make the dependency update pass; preserve existing style and structure.
- If unsure whether a change is safe, leave the PR open with a comment instead of merging.

## Usage

Ask the agent to "process the open dependabot PRs" (optionally limit to a module, e.g. "process dependabot PRs for apps/web").
