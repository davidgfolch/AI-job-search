---
name: dependabot-agent
description: Process open GitHub Dependabot PRs on a local checkout: check the library changelog for breaking changes, make required changes and build, run all tests, sandbox-build the affected docker-compose services, check the logs for failures, and verify the GitHub pipeline completes. Requires the GitHub CLI (gh). Master is never pushed to directly — the persistent staging→master PR handles promotion.
---

# Dependabot Agent Instructions

This skill automates the handling of Dependabot PRs in this monorepo. Dependabot opens PRs against the `staging` branch (see `.github/dependabot.yml`), grouping minor/patch updates per ecosystem. A workflow (`.github/workflows/dependabot-auto-merge.yml`) auto-merges grouped `minor-patch`/`github-actions` PRs once CI is green, but it **skips semver-major PRs** and any PR whose CI fails. This agent acts where automation cannot: it does the changelog sanity check, runs the module tests locally, builds the affected docker-compose services, verifies the logs, fixes failures, and pushes to the PR branch so auto-merge can proceed. It never pushes to `master`.

## Prerequisites

- GitHub CLI installed and authenticated: `gh auth status`.
- Local env ready: `docker-compose up -d` (MySQL) and `.env.secrets` present (copy `scripts/.env.secrets.example` if missing — **never commit it**).
- Clean working tree on `staging`.

## Workflow

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

3. **Checkout the PR branch**:
   ```bash
   gh pr checkout <n>
   ```

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
# Windows
.\scripts\test.bat <module>
# Linux/Mac
./scripts/test.sh <module>
```
For a `commonlib` bump run the full Python dependent set, e.g. `.\scripts\test.bat commonlib backend scrapper aiEnrich aiEnrichNew aiEnrichSkill aiEnrich3 aiCvMatcher aiFormFiller cron`.

### 5. Sandbox build the affected docker-compose services and check logs

Run the docker verification in an **isolated sandbox project** so the live `ai-job-search-*` stack and its data are never touched. The sandbox uses `docker-compose.test.override.yml` (renamed `-test` containers, remapped ports, data isolated under `.docker-sandbox/`). The scripts handle build, MySQL clone, log check, and teardown:

```bash
# Windows
.\scripts\test-sandbox.bat <service>
# Linux/Mac
./scripts/test-sandbox.sh <service>
```

- Use the affected composed service name, e.g. `backend` or `web`. The script brings up only that service plus its DB dependencies in the isolated `dependabot-test` project. The `aiEnrich*` workers (`aienrich`, `aienrichnew`, `aienrichskill`, `aienrich3`) and `aicvmatcher` are also defined in the sandbox override; the `aiEnrich*` ones are profile-gated in the base file, so pass their profile, e.g. `.\scripts\test-sandbox.bat --profile aiEnrichNew aienrichnew`.
- **MySQL data clone**: for `backend`, the script dumps the live `jobs` DB (`scripts/mysql/backup.*`) into `scripts/mysql/backups/`, then restores it into the sandbox mysql container. Skip with `--no-db-clone`.
- **Mongo**: the sandbox spins a fresh, empty Mongo seeded by `scripts/mongo/init.js` (full isolation) — the base full-stack Mongo is never touched.
- **Ollama/prometheus/grafana are never duplicated**: they are not defined in the override. The sandbox runs services whose dependency graph avoids ollama (`backend`, `web`, `aienrichnew`, `aienrich3`, `aicvmatcher`, `cron`).
- **Ollama-dependent services** (`aienrich`, `aienrichskill`, `scrapper`): do a **build-only** check (never `up`) and rely on the module unit tests + the GitHub `ci-gate` for runtime validation. Example:
  ```bash
  docker compose -f docker-compose.yml -f docker-compose.test.override.yml -p dependabot-test build <service>
  ```
  Then tear the project down (the wrapper's teardown only covers `up`-based runs).
- Skip this step entirely for a module that never runs in the compose stack (e.g. pure `apps/e2e` only).
- **Check for startup success and errors** in the sandbox:
  ```bash
  docker compose -p dependabot-test ps                 # sandbox services should be Up (healthy)
  docker compose -p dependabot-test logs <service> --tail=100
  ```
  Treat container restart loops, non-zero exits, failed healthchecks, or error-level stack traces as red flags requiring investigation before committing.
- The wrapper tears down the sandbox (removes containers, the `mongo_data_sandbox` volume, and the `.docker-sandbox/` dir) on exit unless `--keep` is passed.

### 6. Green result

- Regenerate/commit any lockfile/badge churn the test run produced (e.g. `poetry.lock`, `uv.lock`, `package-lock.json`):
  ```bash
  git add -A && git commit -m "chore: regenerate lockfile for <module>" && git push
  ```
- **Check GitHub pipeline completion** — this is the acceptance gate. Wait for CI and confirm the final `ci-gate` job (from `ci.yml`) passes:
  ```bash
  gh pr checks <n> --watch
  ```
  Only treat the PR as green when the run is complete and `ci-gate` succeeded (and docker/log checks above passed).
- For auto-merge-eligible PRs, verify merge is enabled — the merge to staging happens automatically once checks pass:
  ```bash
  gh pr view <n> --json state,mergeStateStatus,autoMergeRequest
  ```
- For PRs that are not auto-merge eligible (semver-major guard, or ungrouped PR reviewed by a human), merge explicitly only when checks and `ci-gate` are green:
  ```bash
  gh pr merge <n> --squash
  ```
- Post a short summary comment on the PR documenting what changed and that docker/log/pipeline checks passed.

### 7. Red result

- Read the failure output. Common causes: API/code breaking changes in a new version, a too-narrow dependency constraint, or lockfile churn.
- Fix only what is required to make the module green: bump constraints in the module's `pyproject.toml`/`package.json`, or patch code/tests for the new version.
- Re-run the module tests (`.\scripts\test.bat <module>`), then run the architecture checks if code changed:
  ```bash
  # Python apps
  poetry run pytest apps/commonlib/commonlib/test/architecture_test.py
  # Web app
  npx vitest run src/test/architecture.test.ts   # from apps/web
  ```
- Re-run step 5 (sandbox build + logs via `scripts/test-sandbox.*`) after a code/constraint fix if the affected service is a composed one.
- Commit + push and re-verify until green.
- If the failure cannot be fixed within reasonable effort, post the diagnosis and leave the PR open:
  ```bash
  gh pr comment <n> --body "<root cause and what was tried>"
  ```

### 8. Wrap-up

- Return to a clean state:
  ```bash
  git checkout staging && git pull
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
- Never commit `.env.secrets` or any credentials.
- Only change code required to make the dependency update pass; preserve existing style and structure.
- If unsure whether a change is safe, leave the PR open with a comment instead of merging.

## Usage

Ask the agent to "process the open dependabot PRs" (optionally limit to a module, e.g. "process dependabot PRs for apps/web").
