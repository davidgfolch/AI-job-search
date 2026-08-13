# GitHub Automation (CI, Dependabot & Auto-merge)

All GitHub-side automation of the monorepo: the CI pipeline, Dependabot version updates, and automatic merging of dependency PRs.

## CI / GitHub Actions Pipeline

The CI workflow (`.github/workflows/ci.yml`) only tests the modules affected by a change, instead of always running the full matrix.

### How it works

1. A `changes` job uses [`dorny/paths-filter`](https://github.com/dorny/paths-filter) to detect which `apps/*` modules were modified in the push/PR.
2. It builds a dynamic test matrix containing exactly those modules, so unchanged apps are never executed.
3. The `test` job runs the matrix (`npm test`, `uv run pytest`, or `poetry run pytest` depending on the module) and uploads a coverage badge artifact per module.
4. On `master`, an `update-badges` job downloads the artifacts and commits any changed coverage badges back to the repo.

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

### Grouping strategy

Non-breaking updates are grouped per app into a single PR via a `minor-patch` group (`update-types: [minor, patch]`), so instead of one PR per dependency there is roughly one per app per day. Major version bumps stay in separate PRs for review. All GitHub Actions updates group into one weekly PR.

> **Note:** YAML anchors/aliases are **not supported** by Dependabot (`dependabot-core#1582`), so the `groups` block is intentionally repeated on each update entry.

### Adding a new app

Add an `updates` entry for the app's package manager (`npm` or `pip`). For `pip` apps, keep the `ignore` rule for the local `commonlib` dependency so Dependabot never tries to bump it to a registry version. Include the same `groups.minor-patch` block as the other entries.

## Auto-merge

The `.github/workflows/dependabot-auto-merge.yml` workflow enables GitHub's native auto-merge for every PR labeled `dependencies`.

### Behavior

- It runs when a Dependabot PR is opened, labeled, updated, or reopened against `master`.
- It enables auto-merge with **squash** merging.
- GitHub only performs the merge once **all required checks pass** (green CI).
- **A PR that fails CI simply never merges** — it stays open for a human to handle. There is no agent and no automatic fix attempt.

### Prerequisites (one-time, repo admin)

1. **Repo Settings → General → Pull Requests**: enable **"Allow auto-merge"**.
2. Create a **branch protection rule / Ruleset** on `master` that **requires the `CI` check** (at least one requirement). Without a branch protection requirement the action cannot enable auto-merge (and would merge immediately if the PR is already mergeable).

### Notes & caveats

- The workflow uses the default `GITHUB_TOKEN`, so the resulting merge does **not** trigger further workflow runs (e.g. the `update-badges` job on `master` won't run after a Dependabot merge). To trigger them, replace `secrets.GITHUB_TOKEN` with a `repo`-scoped PAT secret.
- A `commonlib` bump runs the full Python test matrix (all dependents), so those PRs take longer to reach green but still auto-merge when they pass.
- The CI `test` job runs `poetry lock` for `commonlib`/`scrapper`; if you see lockfile churn on Dependabot branches, that regeneration is the cause.
