---
trigger: always_on
---

## Documentation Policy

Keep documentation accurate and useful. Prefer fixing only what's wrong over documenting every change.

Workflow: use the `docs-writer` skill (`.claude/skills/docs-writer/SKILL.md`) — short root README, one canonical source per fact linked instead of copied, and operations documented through the centralized `scripts/*` entry points.

### When to update docs

- **Fix if wrong**: If your change makes existing documentation factually incorrect, fix it in the same session.
- **User-visible/setup changes**: Update `README.md` and/or `apps/<module>/README.md` only for user-visible features, UI flows, setup/install steps, or breaking configuration changes.
- **Agent/SDLC systems**: Changes to hooks, rules, plugins, skills, guards, or workflows → update `READMEs/AGENTIC_SDLC.md` and the relevant file in `.claude/rules/`. Don't require updating root `README.md`, `AGENTS.md`, or `.claude/CLAUDE.md` for every mechanical change.
- **Internal changes**: Refactors, tests, internal implementation details → no doc updates required. Use [CodeGraph](https://github.com/colbymchenry/codegraph) to locate code/behavior.
- **Plans/TODO**: Only update plan files or `READMEs/TODO.md` if the status/outcome actually changes or an item is closed.

### Guidelines

- **Root README**: High-level overview, features (high-level), quick start, Docker/native usage, and links to detailed docs. Avoid deep implementation mechanics (discovery internals, watchdog details, etc.).
- **App READMEs** (`apps/*/README.md`): Purpose, quick start/run instructions, minimal configuration. Link to `READMEs/AGENTIC_SDLC.md` or code for internals.
- **Single source of truth**: Don't duplicate rule/hook/guard details across `README.md`, `AGENTS.md`, `.claude/CLAUDE.md`. Link to `READMEs/AGENTIC_SDLC.md` and `.claude/rules/`.
- **Be concise**: Prefer short notes with links over long explanations. Docs should explain setup/usage and high-level architecture, not duplicate implementation details.
- **Don't document what the code already says**: module READMEs cover purpose, user-visible behaviour, configuration knobs, defaults and setup/run steps.
  Selectors, internal call chains, retry counts, fallback ordering, log event tables and implementation rationale belong in code, comments and tests — never in a README.
  Link to the source or a cross-cutting doc instead of restating it.
- **Code owns contracts**: `scripts/mysql/ddl.sql` owns SQL DDL; route handlers and tests own API endpoints and JSON request/response shapes.
  A README may name the capability and link to the source (or use CodeGraph), but must not copy DDL, endpoint tables or payload examples.
- **Fix only what's necessary**: Preserve untouched wording/structure. Don't restyle or rewrite unrelated sections.
- **Use CodeGraph first**: For locating code/behavior, use CodeGraph before grepping/reading files. Documentation is not a code index.
- **Generated files**: `.codegraph/` is machine-local generated output — never hand-edit, never commit, never count as documentation.
- **Code comments/docstrings**: Fine for implementation; markdown docs explain usage/setup.

### Reminders
Hooks/plugins may remind you to check docs, but they are not mandatory update triggers. Only update docs if they are inaccurate or if the change is user-visible/setup-related per the rules above. If docs are checked and no changes are needed, say so briefly in your summary.
