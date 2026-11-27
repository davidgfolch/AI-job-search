---
name: parallel-dev
description: Run feature/fix work in a throwaway sibling clone using scripts/dev.sh (or scripts/dev.bat) so the main workspace, its branches, lockfiles, and running stack stay untouched. Use when starting parallel development, isolating risky changes, or preparing a PR from a clean clone.
---

# Parallel Development (Sibling Clones)

Use the centralized dev workflow to work in sibling clones beside the main repo. Each clone is named `ai_job_search-*` under the same parent directory and is managed only through `scripts/dev.sh` / `scripts/dev.bat`.

## Why

- Main workspace stays untouched: no branch switching, no lockfile churn, no stack disruption.
- Each task gets an isolated git checkout and runtime state.
- Clones can be tested, sandboxed, pushed, PR'd, merged, and deleted independently.

## Prerequisites

- Run commands from the repo root or any managed clone.
- Git remote configured; `gh` authenticated for `pr`/`merge`/`dep`.
- Main workspace may contain `.env.secrets`, lockfiles, `node_modules`, and `.codegraph/codegraph.db`; `new`/`dep` copy runtime state into the clone.

## Commands

Linux/Mac: `./scripts/dev.sh <command> [args]`  
Windows: `.\scripts\dev.bat <command> [args]`

| Command | Purpose |
|---|---|
| `new <name>` | Clone `../ai_job_search-<name>`, create `feat/<name>` from `master`, copy runtime state, sync deps offline when possible. |
| `dep <pr>` | Clone `../ai_job_search-dependabot-<pr>`, check out PR, refresh deps/CodeGraph for manifest changes. Used by `dependabot-agent`. |
| `list` | Show sibling clones. |
| `status` | Show branch, dirty state, ahead/behind vs `master`. |
| `checkout <branch>` | Switch branch inside the current clone. |
| `test [modules]` | Run `scripts/test.sh` in the current clone. No args runs the full suite. |
| `sandbox <service> [...]` | Run `scripts/test-sandbox.sh` in the current clone. Only one sandbox at a time (`dependabot-test` fixed project/ports). |
| `commit "msg"` | `git add -A && git commit -m ...` in the current clone. |
| `push` | Push current branch; refuses `staging`/`master`. |
| `pr [title] [--base br]` | Create PR; default base `master`. Refuses PR from `staging`/`master`. |
| `merge [-k]` | Wait for green checks, squash-merge PR, delete remote branch and local clone. `-k` keeps clone. |
| `sync` | Fast-forward `staging` from `master` and push. For Dependabot gate sessions; stops on divergence. |
| `cleanup <name\|path>` | Delete a sibling clone by name/prefixed name/path. Refuses non-clone targets. |

## Typical Feature Flow

```bash
./scripts/dev.sh new my-feature
cd ../ai_job_search-my-feature

# work...
./scripts/dev.sh test commonlib <affected-apps>
./scripts/dev.sh commit "feat: describe change"
./scripts/dev.sh push
./scripts/dev.sh pr "feat: describe change"
./scripts/dev.sh merge
```

## Typical Dependabot Flow

Use the `dependabot-agent` skill for full Dependabot handling. The clone commands are:

```bash
./scripts/dev.sh new dependabot-session
cd ../ai_job_search-dependabot-session
./scripts/dev.sh sync

./scripts/dev.sh dep <pr>
cd ../ai_job_search-dependabot-<pr>
# validate/fix, then push/merge per dependabot-agent
```

## Safety Rules

- Never work directly in the main workspace for parallel tasks when a clone is appropriate.
- Never delete arbitrary directories; use `cleanup` so only `ai_job_search-*` siblings are removed.
- `merge` and `cleanup` refuse unsafe targets; keep a clone with `-k` when inspection is needed.
- Run tests through centralized scripts (`scripts/test.sh` / `scripts/test.bat`), always include `commonlib` when code/tests changed.
- For sandbox verification, use `scripts/test-sandbox.*` via `dev ... sandbox`; it isolates Docker project/data from the live stack.
- `sync` is only for moving the Dependabot gate (`staging`) forward from `master`; resolve divergence manually, do not create merge commits from the script.