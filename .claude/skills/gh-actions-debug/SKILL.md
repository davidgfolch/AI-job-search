---
name: gh-actions-debug
description: Debug GitHub Actions / Dependabot run failures with the gh CLI. Use when a workflow run fails, a status check is red, or a Dependabot security/version update errors out.
---
# Debug GitHub Actions & Dependabot Runs with `gh`

The `gh` CLI surfaces the full logs that the GitHub web UI hides (Dependabot run logs, step annotations, job-level detail). Prefer `gh` over `webfetch` when investigating any run failure.

## Inspect an Actions run

```bash
# Overview + status
gh run view <run-id> --repo <owner>/<repo>

# Full logs (quietest source of truth; includes the JSON job definition for Dependabot)
gh run view <run-id> --repo <owner>/<repo> --log

# Only the failed steps' logs
gh run view <run-id> --repo <owner>/<repo> --log-failed

# Machine-readable summary + job list
gh api repos/<owner>/<repo>/actions/runs/<run-id>
gh api repos/<owner>/<repo>/actions/runs/<run-id>/jobs
gh api repos/<owner>/<repo>/actions/runs/<run-id>/jobs --jq '.jobs[] | {name, status, conclusion}'
```

When no run-id is handy, list recent runs: `gh run list --repo <owner>/<repo> --limit 10` (add `--workflow <name>` to filter).

## Dependabot update-run failures

Dependabot update runs live under the workflow named after the update (e.g. `pip in /apps/scrapper for pytest`). The linked `network/updates/<id>` page requires write access to the repo — but `gh run view <run-id> --log` returns the **same updater output publicly**.

Debug procedure:

1. **Classify the job** — read the `Job definition: {...}` JSON line. Key fields:
   - `command`: `"security"` = Dependabot security advisory (auto-generated run), vs a normal version bump.
   - `security-advisories`: e.g. `{"dependency-name":"pytest","affected-versions":["< 9.0.3"]}`.
   - `package-manager` + `source.directories`: which manifest/ecosystem was scanned.
2. **Find the real error** — search the log for the error table after "Dependabot encountered 'N' error(s)":
   - `type` (e.g. `dependency_file_not_supported`) and `details` name the offending dependency.
3. **Recognize common failure modes**:
   - `dependency_file_not_supported` + *"can't update vulnerable dependencies for projects without a lockfile or pinned version requirement as the currently installed version of <pkg> isn't known"* → the manifest uses a **floating/range constraint** (e.g. `pytest = "^8.4.2"`) and the repo commits **no lockfile**, so Dependabot can't compute the installed version for a *security* fix. Fix: pin the dependency to an exact version (`pytest = "9.1.1"`) or commit the lockfile. Ordinary minor/patch bumps keep working because they only rewrite the constraint — a failing *security* run does not imply the version-bump runs are broken.
   - `failed to update dependency ... requirements could not be satisfied` → a manifest constraint blocks the target version (check the ignore list / range against the advisory's patched version).
4. **Verify the fix** — after pushing the change, check the Dependabot security alerts tab or re-run and confirm the run goes green rather than erroring.

## Tips

- `webfetch` on the run URL only returns the "Error: The updater encountered one or more errors" banner with a write-access link — always fall back to `gh run view <run-id> --log`.
- Dependabot runs may list the trailing `##[error]Dependabot encountered an error performing the update` even when the actual table shows a non-blocking classification; read the table, not just the annotation.