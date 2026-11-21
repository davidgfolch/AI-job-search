---
name: docs-writer
description: Write and update this repository's documentation (root README, apps/*/README.md, READMEs/*, agent docs) under four rules: keep the root README short, keep one canonical source per fact and link instead of copying (DRY), document every operation through the centralized scripts/* entry points, and never document what the code already says.
---
# Docs Writer Instructions

Use this skill whenever you add, rewrite or review documentation. It complements (and never overrides) the always-on policy in `.claude/rules/documentation-update.md`; read that rule first and apply both.

## The four rules (non-negotiable)

### 1. The root `README.md` stays short

The root README is the front page: overview, high-level features, quick start and links. It must not grow implementation detail.

- One bullet per feature, one or two lines, ending in a link to the doc that owns the detail.
- No fallback chains, env-var tables, probe/timeout internals, troubleshooting blocks or per-topology command blocks. Those belong to `READMEs/*` or `apps/<module>/README.md`.
- When a section becomes longer than a short paragraph plus a link, move the body to a `READMEs/*` doc and leave the pointer behind.
- Delete sections whose detail now lives elsewhere instead of keeping a shortened copy.

### 2. Single source of truth: DRY, link to the existing doc

Every fact has exactly one owner. Before writing a sentence, find out whether it is already documented and link to it.

- Owner selection: user-visible behaviour and setup → `README.md` / `apps/<module>/README.md`; cross-cutting mechanics, topologies, agent/SDLC systems → the matching `READMEs/*.md`; rules and guardrails → `.claude/rules/`; commands → `scripts/*`.
- Repeating a fact in a second file is a bug: replace the copy with a relative link, e.g. `[Distributed execution & LAN service auto-discovery](../../../READMEs/DISTRIBUTED_EXECUTION.md)`.
- Fix wrong statements in the owning doc, then make sure the linking docs do not restate them.
- Keep link text consistent across files so the same target is recognizable everywhere.
- Never document `.codegraph/`, `data/`, `node_modules/` or other generated output.

### 3. Operations are documented through the centralized `scripts/*` entry points

The repository centralizes install, test, lint, sandbox, dev-clone and uninstall workflows in `scripts/`. Documentation must point there, never at raw package-manager commands.

| Never document as the way to do it | Document instead |
|---|---|
| `poetry run pytest`, `uv run pytest`, `npm test` | `./scripts/test.sh [commonlib <apps>]` / `.\scripts\test.bat ...` |
| `poetry install`, `uv sync`, `npm install`, `pip install` per app | `./scripts/install.sh` / `.\scripts\install.bat` |
| `ruff ...`, `npx eslint`, `npx tsc` | `./scripts/lint.sh [python\|web\|e2e]` / `.\scripts\lint.bat` |
| `docker compose up` for an isolated check | `./scripts/test-sandbox.sh <service>` / `.\scripts\test-sandbox.bat <service>` |
| ad-hoc sibling `git clone`/`worktree` for feature or Dependabot work | `./scripts/dev.sh <new\|dep\|sync\|cleanup\|test\|sandbox\|commit\|push\|pr\|merge\|list\|status>` / `.\scripts\dev.bat ...` |
| manual removal of containers, venvs, volumes, indexes | `./scripts/uninstall.sh` / `.\scripts\uninstall.bat` |
| `uv tool install ruff` / `codegraph install` by hand | `scripts/install.*` (it installs host tools) |

Rules that follow from this:

- Each script is documented once, where it is introduced (`READMEs/README_INSTALL.md`, `READMEs/README_DEVELOPMENT.md`, `READMEs/README_GITHUB.md`, `AGENTS.md`); other docs link to that place.
- Respect the "do not run the raw package manager" policy: a documented command must be copy-pasteable from the repo root.
- If a script does not exist yet, either add it under `scripts/` (both `.sh` and `.bat`) or document the operation as a one-off with an explicit caveat — never invent a `scripts/` command.
- `docker compose` snippets are fine for starting the stack (`docker-compose up -d --build <service>`); anything that isolates, tests or cleans up goes through `scripts/*`.

### 4. Don't document what the code already says

A README explains how to use a module, not how it is built. If a sentence is verified by reading the implementation — selectors, class or function names in a call chain,
retry counts and timeouts, fallback ordering, cache TTLs, log event names, or "we do X because Y broke" — it does not belong in documentation.
The code, its comments and its tests own it.

- Document observable behaviour, configuration knobs and defaults, setup/run steps and links to canonical cross-cutting docs.
- Delete implementation detail; do not shorten it into a still-detailed paragraph. A link to the source file is enough when a pointer is needed.
- Code owns contracts: `scripts/mysql/ddl.sql` owns SQL DDL; route handlers and tests own API endpoints and JSON request/response shapes.
  Name the capability and link to the source or CodeGraph; never copy DDL, endpoint tables or payload examples into a README.
- Per-site DOM layouts, scraper selector strategies and anti-bot workaround mechanics are code concerns. A site status plus the relevant env var is enough.
- When a change makes such a passage stale, remove it instead of updating it.

## Document map

| Concern | Owner |
|---|---|
| Overview, features, quick start, links | `README.md` |
| Install, dependencies, env, Docker sandbox | `READMEs/README_INSTALL.md` |
| Development, tests, lint, coverage, logging | `READMEs/README_DEVELOPMENT.md` |
| Compose services, profiles, service URLs | `READMEs/DOCKER_DEV.md` |
| Distributed execution, LAN auto-discovery, Ollama placement | `READMEs/DISTRIBUTED_EXECUTION.md` |
| CI, Dependabot, branch promotion | `READMEs/README_GITHUB.md`, `.claude/rules/branch-workflow.md` |
| Agent harness, skills, hooks, guards, policy index | `READMEs/AGENTIC_SDLC.md`, `.claude/rules/*.md` |
| Agent command cheat-sheet | `AGENTS.md` / `.claude/CLAUDE.md` |
| Module behaviour, configuration | `apps/<module>/README.md` |

## Workflow

1. **Classify the change.** Is it a user-visible feature, a UI flow, a setup/run step, a cross-cutting mechanic, an agent/SDLC system, or an internal refactor?
   Internals and refactors need no doc change.
2. **Find the owner.** Search existing docs (and CodeGraph for the code behaviour) before writing. Name the file that already owns the fact.
3. **Decide fix vs add, or delete.** If a statement became wrong, correct it where it lives. If something is missing, add it to the owner only.
   If it is duplicated, replace the copy with a link. If it restates implementation detail, delete it.
4. **Write minimally.** Match the surrounding style, headings and wording; do not restyle untouched sections or reorder tables. Keep lines under 200 characters, closing punctuation on the same line, no changelog phrasing ("now also", "as of this PR").
5. **Check the entry points.** Every operational command in the text must exist in `scripts/`, in both `.sh` and `.bat` where the repo provides both, and be invoked from the repo root. Cross-check `scripts/` before quoting a command.
6. **Verify links and anchors.** Every relative link resolves and every `#anchor` matches a real heading (GitHub slug: lowercase, punctuation dropped, spaces to `-`). Relative links from `apps/<module>/README.md` start with `../../`, from `READMEs/*.md` with `./` or `../apps/`.
7. **Report.** In the summary, list the docs updated, or state that none needed changes and why. Documentation-only changes skip the test suites per `.claude/rules/test-enforcement.md` — say so.

## Verification commands

```bash
# Whitespace / conflict markers
git diff --check

# List every relative markdown link that carries an anchor (review the slugs)
grep -rnoE '\]\([^)]+\.md#[^)]+\)' README.md READMEs apps/*/README.md AGENTS.md

# Headings of a target file, to confirm an anchor exists (GitHub slug: lowercase, punctuation dropped, spaces -> -)
grep -n '^#' READMEs/DOCKER_DEV.md

# Stale inbound links after renaming a heading
grep -rn 'old-anchor\|Old Heading' README.md READMEs apps/*/README.md AGENTS.md .claude/

# A documented script really exists (both variants when the repo ships both)
ls scripts/<name>.sh scripts/<name>.bat
```

For the anchor check, compare each `file.md#slug` against the headings of that file (`grep -n '^#' <file>`); fix the link rather than renaming a heading other docs already use.

## Anti-patterns

| Anti-pattern | Why it hurts | Do instead |
|---|---|---|
| A README paragraph that restates selectors, retries, call chains or fix history | Goes stale on the next code change; the code is the source of truth | Delete it; leave a link to the source or the canonical doc |
| A README that copies DDL, an endpoint table or a JSON payload | Duplicates code that CodeGraph and `scripts/mysql/ddl.sql` already own | Delete it; name the capability and link to the source |
| Adding a new section to the root README to explain mechanics | The front page turns into a manual | Put the detail in `READMEs/*` and link to it |
| The same fallback chain / env table in 3–4 files | They drift and disagree | One owner, links everywhere else |
| Leaving a "short version" copy after moving a section | Two sources of truth | Delete it and keep the pointer |
| Documenting `poetry run`, `uv run`, `npm test`, per-app installs | Bypasses the centralized runners and the architecture checks | Document `scripts/test.*`, `scripts/install.*`, `scripts/lint.*` |
| Quoting a `scripts/` command that does not exist | Broken copy-paste | Check `scripts/` or add the script first |
| Adding a changelog or PR narrative | Docs age instantly | Describe current behaviour only |
| Editing `.codegraph/` or other generated output | Regenerated, machine-local | Leave it alone |
| Renaming a heading other docs anchor to | Silently breaks links | Keep the heading, or fix every inbound link |

## Usage

- "Document the new `AI_ENRICH_*` variable" → add it to `apps/aiEnrich/README.md` (owner) and link from the root README only if it is user-visible.
- "The README section about Ollama is huge" → move it to `READMEs/DISTRIBUTED_EXECUTION.md`, leave one feature bullet plus a link in `README.md`, and trim the copies in `DOCKER_DEV.md`, `AGENTS.md` and the module READMEs to pointers.
- "Update the test instructions" → keep the canonical wording in `READMEs/README_DEVELOPMENT.md` and quote `./scripts/test.sh commonlib <apps>`; do not document `uv run pytest`.
- "Explain how Dependabot works" → `.claude/rules/branch-workflow.md` + `READMEs/AGENTIC_SDLC.md` own it; `AGENTS.md` only links.
- "Review this docs-only PR" → check the four rules, then run the verification commands; no test suite needed.
