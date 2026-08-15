---
name: dependabot-agent
description: Process open GitHub Dependabot PRs on a local checkout, run the TDD pipeline for the affected module(s), fix any failures, and get green PRs merged into the staging branch. Requires the GitHub CLI (gh). Master is never pushed to directly — the persistent staging→master PR handles promotion.
---

# Dependabot Agent Instructions

This skill automates the handling of Dependabot PRs in this monorepo. Dependabot opens PRs against the `staging` branch (see `.github/dependabot.yml`). A workflow enables GitHub auto-merge for grouped minor/patch PRs once CI is green, but **PRs that fail CI stay open** — that is where this agent acts: it runs the module tests locally, fixes the failure, and pushes to the PR branch so auto-merge can proceed. It never pushes to `master`.

## Prerequisites

- GitHub CLI installed and authenticated: `gh auth status`.
- Local env ready: `docker-compose up -d` (MySQL) and `.env.secrets` present (copy `scripts/.env.secrets.example` if missing — **never commit it**).
- Clean working tree on `master`.

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
   Map paths under `apps/<name>/**` to the module name (`apps/web` → `web`, `apps/backend` → `backend`, etc.). A `commonlib` bump means all Python dependents must be tested.

2. **Checkout the PR branch**:
   ```bash
   gh pr checkout <n>
   ```

3. **Run the TDD pipeline for the module** (this also regenerates lockfiles/badges like CI does):
   ```bash
   # Windows
   .\scripts\test.bat <module>
   # Linux/Mac
   ./scripts/test.sh <module>
   ```
   For a `commonlib` bump run the full Python dependent set, e.g. `.\scripts\test.bat commonlib backend scrapper aiEnrich aiEnrich3 aiEnrichNew aiEnrichSkill aiCvMatcher aiFormFiller cron`.

### 3. Green result

- Commit and push any lockfile/badge churn the test run produced (e.g. `poetry.lock`, `uv.lock`, `package-lock.json`):
  ```bash
  git add -A && git commit -m "chore: regenerate lockfile for <module>" && git push
  ```
- Wait for CI: `gh pr checks <n> --watch`.
- If auto-merge is enabled (grouped minor/patch), the merge to staging happens automatically once checks pass. Verify:
  ```bash
  gh pr view <n> --json state,mergeStateStatus,autoMergeRequest
  ```
- If auto-merge was not enabled (semver-major guard, or ungrouped PR reviewed by a human), merge explicitly only when checks are green:
  ```bash
  gh pr merge <n> --squash
  ```

### 4. Red result

- Read the failure output. Common causes: API/code breaking changes in a new version, a too-narrow dependency constraint, or lockfile churn.
- Fix only what is required to make the module green: bump constraints in the module's `pyproject.toml`/`package.json`, or patch code/tests for the new version.
- Re-run the module tests (`.\scripts\test.bat <module>`), then run the architecture checks if code changed:
  ```bash
  # Python apps
  poetry run pytest apps/commonlib/test/architecture_test.py
  # Web app
  npx vitest run src/test/architecture.test.ts   # from apps/web
  ```
- Commit + push and re-verify until green.
- If the failure cannot be fixed within reasonable effort, post the diagnosis and leave the PR open:
  ```bash
  gh pr comment <n> --body "<root cause and what was tried>"
  ```

### 5. Wrap-up

- Return to a clean state:
  ```bash
  git checkout master && git pull
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
