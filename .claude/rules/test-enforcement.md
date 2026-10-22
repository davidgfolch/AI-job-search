---
trigger: always_on
---

## The centralized test suite must run after every code or test change

`apps/commonlib/commonlib/test/architecture_test.py` is the **only** place the repository's architecture rules are enforced: file length (200-line soft limit), backend layering, test-file naming, sibling-test correspondence, bare `print()`, and the `console=` logging contract. It lives in commonlib, so it executes **only when commonlib is one of the modules passed to the centralized test script**.

Therefore, after any change to production code or test code, the agent must run the centralized suite through `scripts/test.sh` (Linux/Mac) or `scripts/test.bat` (Windows) — never `poetry run pytest`, `uv run pytest`, or `npm test` directly — and it must always include `commonlib`:

```bash
# Linux/Mac
./scripts/test.sh commonlib <modified apps>
# Windows
.\scripts\test.bat commonlib <modified apps>
```

A runner invocation with **no** targets already executes commonlib first, then every other module, then the e2e suite.

### Which changes require the suites

| Change | Requires the suite |
|--------|--------------------|
| Python source or tests under `apps/**/*.py` | yes |
| Frontend source under `apps/web/src/**` | yes |
| E2E specs under `apps/e2e/**` | yes |
| The test runners themselves (`scripts/test.sh`, `scripts/test.bat`, any `test.*`) | yes |
| Environment files (`.env`, `.env.secrets`, `.env.*`) | yes — they change test behavior |
| Dependency manifests (`pyproject.toml`, `package.json`, `package-lock.json`, `uv.lock`, `poetry.lock`) | yes |
| Other scripts under `scripts/` | yes |
| Documentation (`*.md`, `*.txt`, `*.rst`) | no |
| CI workflows (`.github/workflows/`), coverage gates (`scripts/coverage/`), install/sandbox helpers (`scripts/install.*`, `scripts/uninstall.*`, `scripts/test-sandbox.*`, `scripts/lint.*`), agent rules and skills (`.claude/`, `.opencode/`), generated paths (`data/`, `node_modules/`, `.venv/`, `coverage/`, `.codegraph/`) | no |

When the suites are skipped for one of the excluded categories, state that reason in the final summary.

### Enforcement

The requirement is enforced in the tool call, so it does not depend on the agent remembering it:

| Mechanism | Harness | What it does |
|-----------|---------|--------------|
| `.claude/rules/test-enforcement.md` | all | Canonical policy: which changes require the suite, and how it must be invoked |
| `.claude/hooks/test-enforce.py` | Claude Code (`PreToolUse` on `Edit`/`MultiEdit`/`Write`/`NotebookEdit` and on `Bash`) | Tracks the changed files, adds `commonlib` and the pending modules to a `scripts/test.sh` / `scripts/test.bat` invocation, and injects a reminder with the exact command to run |
| `.opencode/plugins/test-enforce.js` | opencode | Same behavior: injects the missing targets into a test-runner call and prints the reminder once on the next shell call |

Both are registered automatically: the hook in `.claude/settings.json`, the plugin in `.opencode/opencode.json`. They mirror each other.
