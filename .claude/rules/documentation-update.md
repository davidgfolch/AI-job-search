---
trigger: always_on
---

## Documentation Sync (mandatory, automatic)

Documentation is part of the implementation, never a follow-up task. After **every** plan implementation, feature, fix, refactor, config change, or dependency bump, update the affected documentation in the same session, before reporting the work as done. Never wait for the user to ask for it.

This is enforced by a rule (this file) plus reminders: `.claude/hooks/docs-sync.py` (Claude Code) and `.opencode/plugins/docs-sync.js` (opencode) nudge the agent whenever a source file is touched.

### When it applies

- Applies to any change in `apps/**`, `scripts/**`, `docker/**`, `docker-compose*.yml`, `.env*`, `pyproject.toml`/`package.json`, `.github/workflows/**`, `.claude/**`, `.opencode/**`.
- Does not apply to generated or vendored paths (`graphify-out/`, `node_modules/`, `.venv/`, `data/`, caches, lock files) or to changes with no observable behavior (renamed local variable, formatting, comments).

### Doc map: which docs to update for which change

| Change | Documentation to update |
|--------|--------------------------|
| Behavior, feature, or bug fix inside `apps/<module>/` | `apps/<module>/README.md` |
| New, renamed, or removed module under `apps/` | root `README.md` (Project Structure), `AGENTS.md`, `.claude/CLAUDE.md`, `READMEs/AGENTIC_SDLC.md` (Skills) |
| Env var added/renamed/removed (`.env`, `scripts/.env.secrets.example`, `commonlib/environmentUtil.py`) | root `README.md` (Settings), affected `apps/<module>/README.md` |
| Docker service, profile, port, volume, healthcheck, or `extra_hosts` | `READMEs/DOCKER_DEV.md`, root `README.md` (Docker Compose Profiles), `AGENTS.md` (Ollama host vs container, sandbox sections) |
| Build, test, install, or run command changed | `AGENTS.md`, `.claude/CLAUDE.md`, `READMEs/README_DEVELOPMENT.md` |
| New host requirement (Docker, `gh`, Ollama model, package manager) | `READMEs/README_INSTALL.md` |
| New/changed backend endpoint or DB schema | `apps/backend/README.md` |
| User-visible UI flow, feature, or screenshot-worthy screen | root `README.md` (Features, Screenshots) |
| CI workflow, Dependabot, or branch-flow behavior | `READMEs/README_GITHUB.md` |
| Agent skill, rule, hook, or plugin added/changed | `READMEs/AGENTIC_SDLC.md`, `AGENTS.md` (Skills), `.claude/CLAUDE.md` (Skills) |
| Plan implemented from `.opencode/plans/**` | the plan file itself (`Status:` + outcome notes) and `READMZs/TODO.md` when the item is closed |

### Definition-of-done checklist (before reporting done)

1. Identify the doc-map row(s) matching the change and open every listed file.
2. Fix only what the change made inaccurate. Preserve untouched wording, formatting, and structure (no restyling, no rewrites of unrelated sections).
3. Keep every command/config snippet copy-pasteable and consistent with the current scripts, compose file, and `.env`.
4. If a listed doc needs no change, say so in the final summary ("docs checked, none needed") so the omission is deliberate.
5. List the documentation files updated in the final summary, alongside the code changes.

### Rules

- Document what the code does **after** the change; never describe intended behavior or speculate.
- Markdown under `READMZs/`, the root `README.md`, and `apps/*/README.md` is the documentation surface. Code comments, docstrings, and test names are not a substitute.
- `graphify-out/` is generated output: refresh it with the wrapper (`scripts\graphify\graphify.bat update .`) but never hand-edit it, and never count it as documentation.
- Plan files in `.opencode/plans/**` must be marked with their real outcome; a plan left as "proposed" after implementation is stale documentation.
- If the change makes existing documentation wrong, fixing it is part of the task, not a separate request.
