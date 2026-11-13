---
trigger: always_on
---

## Branch workflow: `master` by default, `staging` only for Dependabot

`master` is the integration branch and the default place for **every non-Dependabot change** (features, fixes, docs, CI, agent rules). `staging` exists **only** as the Dependabot gate: Dependabot opens PRs against it (`.github/dependabot.yml`) and a persistent `staging → master` PR promotes the validated batch.

| Session | Working branch | Start | End |
|---|---|---|---|
| Dependabot processing | `staging` | Sync `master` → `staging` | Promote `staging` → `master` when green |
| Anything else | `master` | `git pull --ff-only` | Commit and push to `master` |

### Session start

- **Dependabot session** — before touching any PR, sync `master` into `staging` so the gate starts from the current release state. Use the repo helper when the branches can fast-forward:
  ```bash
  ./scripts/dev.sh sync        # Windows: .\scripts\dev.bat sync
  ```
  It fast-forwards `staging` to `master` and pushes only when it advanced. If it reports divergence (non-Dependabot work landed on `master`, or a promotion is mid-flight), merge `master` into `staging` and push instead — the gate must sit on current `master`:
  ```bash
  git checkout staging && git pull --ff-only origin staging
  git merge origin/master
  git push origin staging
  ```
  Then process the PRs with the `dependabot-agent` skill.
- **Any other session** — work on `master`:
  ```bash
  git checkout master && git pull --ff-only
  ```
  Never start a feature/fix on `staging`, even if `staging` happens to be checked out.

### Session end

- **Dependabot session, everything green** — promote the gate through the persistent `staging → master` PR (find its number with `gh pr list --base master --head staging`):
  ```bash
  gh pr checks <n> --watch                                                # wait for ci-gate
  ```
  Auto-merge (squash) lands it once the full matrix is green. If no promotion PR is open and `staging` is ahead of `master`, create it and enable auto-merge (see the skill). If it reports `DIRTY`, merge `origin/master` into `staging` and push. Once the promotion lands, sync both local branches to the same commit:
  ```bash
  git checkout master && git pull --ff-only
  git checkout staging && git merge --ff-only master
  ```
- **Dependabot session, something red** — **do not promote**: leave `staging` with the failing batch and the promotion PR open (auto-merge simply does not fire), and report the failure. `master` stays clean and deployable.
- **Any other session** — commit and push to `master` directly (a maintainer may push; the required `ci-gate` check gates the promotion PR, not local work). `staging` is brought up to date by the next Dependabot session start.

### If non-Dependabot changes land on `staging`

They do not belong there. Promote them to `master` immediately (merge `staging` into `master` through the promotion PR, or cherry-pick the commits), then fast-forward `staging` to `master` so the gate starts clean.
