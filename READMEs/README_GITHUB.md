# GitHub Automation (CI, Dependabot & Auto-merge)

All GitHub-side automation of the monorepo: the CI pipeline, Dependabot version updates, and automatic merging of dependency PRs.

## CI / GitHub Actions Pipeline

The CI workflow (`.github/workflows/ci.yml`) only tests the modules affected by a change, instead of always running the full matrix.

### How it works

1. A `changes` job uses [`dorny/paths-filter`](https://github.com/dorny/paths-filter) to detect which `apps/*` modules were modified in the push/PR.
2. It builds a dynamic test matrix containing exactly those modules, so unchanged apps are never executed.
3. The `test` job runs the matrix (`npm test`, `uv run pytest`, or `poetry run pytest` depending on the module) and uploads a coverage badge artifact per module.
4. On `master`/`staging`, an `update-badges` job downloads the artifacts and commits any changed coverage badges to a dedicated `badges` branch (not the protected `master`), which the README badge images load from.

### Change detection rules

- **Per-module**: a change under `apps/<name>/**` triggers tests only for that module.
- **Dependency propagation**: a change to `apps/commonlib` also triggers all modules that depend on it (everything except `apps/web`, which only talks to the backend via REST).
- **Infrastructure**: changes to `.github/**`, `docker-compose.yml`, `pyproject.toml`, `poetry.lock`, or `uv.lock` run the full matrix as a safety net.
- **Excluded**: changes under `scripts/` (not used by the pipeline) trigger nothing.
- If no relevant files changed, the matrix is empty and the `test` job is skipped entirely.

## Dependabot

The configuration lives in `.github/dependabot.yml`.

### Ecosystems & cadency

- **`npm`** — `apps/web`, `apps/e2e` (daily).
- **`pip`** — all Python apps (daily): `commonlib`, `scrapper`, `backend`, `aiEnrich`, `aiEnrichNew`, `aiEnrichSkill`, `aiEnrich3`, `aiCvMatcher`, `aiFormFiller`, `cron`.
- **`github-actions`** — the repository root (weekly), so the CI workflows themselves stay up to date.
- Every Dependabot PR is labeled `dependencies` and each update is capped at 5 open PRs.
- **All PRs target the `staging` branch** via `target-branch: "staging"` on every update entry. Nothing from Dependabot is ever merged straight into `master`.

### Grouping strategy

Non-breaking updates are grouped per app into a single PR via a `minor-patch` group (`update-types: [minor, patch]`), so instead of one PR per dependency there is roughly one per app per day. Major version bumps stay in separate PRs for review. All GitHub Actions updates group into one weekly PR.

> **Note:** YAML anchors/aliases are **not supported** by Dependabot (`dependabot-core#1582`), so the `groups` block is intentionally repeated on each update entry.

### Adding a new app

Add an `updates` entry for the app's package manager (`npm` or `pip`). For `pip` apps, keep the `ignore` rule for the local `commonlib` dependency so Dependabot never tries to bump it to a registry version. Include the same `groups.minor-patch` block as the other entries.

## Auto-merge (staging gate)

Merging into `master` is protected by a **staging gate**. Dependency updates flow:

```
dependabot PR ──auto-merge──▶ staging ──persistent PR + auto-merge──▶ master
```

The `.github/workflows/dependabot-auto-merge.yml` workflow enables GitHub's native auto-merge for every PR labeled `dependencies` **against `staging`**.

### Behavior

- It runs when a Dependabot PR is opened, labeled, updated, or reopened against `staging`.
- It only acts on **grouped** minor/patch PRs (branch names contain the group identifiers `minor-patch` or `github-actions`).
- It enables auto-merge with **squash** merging.
- GitHub only performs the merge once **all required checks pass** (green CI).
- A semver-major guard scans the PR body for `version-update:semver-major` and **skips** auto-merge for those PRs, so a major that slips into a grouped PR still needs a human/agent.
- **A PR that fails CI simply never merges** — it stays open for the agent (the `dependabot-agent` skill in `.claude/skills/`, see [AGENTIC_SDLC.md](AGENTIC_SDLC.md)) to fix locally and push, or for a human to handle.
- **Major version bumps never auto-merge.** They are raised as separate, ungrouped PRs (branch contains the dependency name) and stay open for manual review and merge.

### Promotion to master

- A **persistent `staging → master` PR** is kept open with native auto-merge (squash) enabled. GitHub re-evaluates it on every push to `staging`, so each validated batch is promoted automatically once the **full** CI matrix + e2e is green.
- A regression on `staging` simply keeps that PR open — `master` stays clean and deployable.
- Nothing writes to `master` except this PR's merge. Coverage badges are pushed to the dedicated `badges` branch by `update-badges`, so `master`'s required status checks (`ci-gate`) are never violated.

### Sandbox verification (mandatory dependabot-agent gate)

Before a Dependabot PR is merged, the agent **builds and runs** every affected compose service in an isolated sandbox and verifies the logs are error-free. The sandbox is powered by `scripts/test-sandbox.*` + `docker-compose.test.override.yml` in the `dependabot-test` project:

- Containers are renamed `ai-job-search-test-*`, host ports are remapped (`mysql 13306`, `mongo 17017`, `backend 18000`, `web 15173`, `aiformfiller 18080`), data lives in `.docker-sandbox/`, and ollama/prometheus/grafana are never duplicated.
- **No autodiscovery**: every interacting URL is pinned to deterministic sandbox addresses (`web BACKEND_URL=http://backend:8000`, `COMMONLIB_DB_HOST=mysql_db`, `MONGO_URI=… mongo_db:27017`, and `host.docker.internal` for services not deployed, e.g. ollama). `COMMONLIB_DB_DISCOVERY=False` prevents commonlib from LAN-scanning for MySQL (which would otherwise find the live DB on the docker bridge).
- Modules disabled in `.env` (`AI_*`/`AI_ENRICH*` flags) are **build-only**; `aienrich`/`aienrichskill`/`scrapper` (ollama-dependent) are build-only.
- The live MySQL `jobs` DB is dumped and restored into the sandbox (schema-only init + authenticated readiness check) so data-dependent services run on real data.
- **Any sandbox error aborts the dependabot process**: a failed build, a service not healthy, or `ERROR/CRITICAL/Traceback` in the logs means the PR is not merged until the underlying cause is fixed.

### Prerequisites (one-time, repo admin)

1. **Repo Settings → General → Pull Requests**: enable **"Allow auto-merge"**.
2. Create the `staging` branch from `master`.
3. Add a **branch protection rule / Ruleset** on `master` that **requires the `CI` check**. Without a branch protection requirement the auto-merge action cannot enable auto-merge.
4. Create a fine-grained PAT with `contents: write` and `pull-requests: write` on this repo, and store it as the `AUTOMERGE_TOKEN` secret. It is used by `dependabot-auto-merge.yml` and when enabling auto-merge on the persistent `staging → master` PR, so the resulting merges **do** trigger downstream workflows (badges, promotion re-checks).
5. Create the persistent `staging → master` PR and enable auto-merge on it with the PAT:
   ```bash
   gh pr create --base master --head staging --title "chore: promote staging to master" --body "Auto-merge gate: promotes staging to master when the full CI matrix + e2e are green."
   gh pr merge <number> --auto --squash --admin
   ```

### Notes & caveats

- If Dependabot fails to group an update (rare grouping edge cases), it falls back to an ungrouped PR, which will **not** auto-merge — conservative by design.
- A `commonlib` bump runs the full Python test matrix (all dependents), so those PRs take longer to reach green but still auto-merge when they pass.
- The CI `test` job runs `poetry lock` for `commonlib`/`scrapper`; if you see lockfile churn on Dependabot branches, that regeneration is the cause. The dependabot-agent skill commits this churn back to the PR branch.
- **Agent integration**: the `dependabot-agent` skill (`.claude/skills/dependabot-agent/SKILL.md`, see [AGENTIC_SDLC.md](AGENTIC_SDLC.md)) processes open dependabot PRs locally — it runs the TDD pipeline for the affected module, sandbox-builds **and runs** the affected docker-compose services, checks logs for errors, fixes failures, and pushes so auto-merge can proceed. Run it on demand with opencode.
