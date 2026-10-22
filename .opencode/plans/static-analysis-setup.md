# Static analysis setup: Ruff for Python, enforced ESLint + typecheck for TypeScript

Status: completed

## Problem

Unused imports and unused method parameters are present across the monorepo and nothing detects them:

- **Python** (8 apps, 490 `.py`, ~38k LOC): no linter is enforced. The root `pyproject.toml` declares `ruff`/`mypy`/`black` as dev dependencies but nothing installs or runs them, and there is no `[tool.ruff]` configuration anywhere. Measured with `ruff check --select F401,F841,ARG,F811,B`: **946 findings** — 255 `F401` unused imports (148 production / 109 test), 445 `ARG` unused arguments, 21 `F841` unused variables, 167 `F811` redefinitions, ~50 bugbear.
- **TypeScript** (`apps/web`, 289 files): ESLint *is* configured (`apps/web/eslint.config.js`, typescript-eslint + react-hooks + react-refresh) but is **not run in CI**, so `npm run lint` fails today with **395 errors / 406 problems** — 30 `no-unused-vars` (5 production / 25 test), 315 `no-explicit-any` (44 production / 271 test), 23 react-hooks, 14 react-refresh.
- **TypeScript types**: `npm run build` is `tsc -b && vite build` and it is **already broken** (761 errors). The Dockerfile only runs `npm run dev`, so CI never sees it. 30 of those errors are `TS6133` unused locals — the same class of defect as the Python findings.
- **`apps/e2e`** (24 files): no ESLint configuration at all.

Two genuine bugs are already visible in the findings:

- `apps/backend/repositories/filter_configurations_repository.py:14` defines `find_all` and **redefines it at line 27** — the first is a dead `pass` stub that is silently shadowed.
- `apps/backend/repositories/queries/view_generator.py:6` imports `get_salary_condition` **twice** from the same module.

An unapplied attempt at this already exists in the repo and is not usable as-is: `sonar-quality-gate-setup-changes.patch` (full SonarQube setup requiring a server, token and scanner).

## Solution

### Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Python config + dependency | Root `ruff.toml`, ruff installed once (`uv tool install ruff`) | Ruff is a zero-dependency single binary; avoids touching 9 `pyproject.toml`/lockfiles and the poetry/uv split between apps |
| First CI gate | Phased: auto-fix first, then gate `F401`/`F841` | 946 findings at once means a red CI nobody reads |
| Type checking | Fix the broken `tsc` build and gate it | `tsc` already catches unused locals (`TS6133`) and costs nothing extra to run |
| Unused arguments | `_name` convention + later `ARG` gate | Distinguishes "intentionally unused" from "forgot to use it" |

### Tooling

- **Ruff** for Python. Not flake8/pylint (slower, more config), not mypy/pyright (only 572 of 3450 functions have return annotations — 17% — so a type checker produces thousands of errors and no signal), not isort (`I` would rewrite every import block in the repo and break the "preserve existing code" rule).
- **ESLint** for TypeScript — already configured, so no new tool; it only needs to be enforced plus a policy for `no-explicit-any`.
- **`tsc -b`** as a typecheck gate, once the existing breakage is fixed.
- **SonarQube** stays in reserve as a later dashboard layer (`sonar-quality-gate-setup-changes.patch`); it catches the same unused-import/unused-parameter classes as ruff but with real infrastructure cost and slower feedback.

### Deliverables

1. **`ruff.toml` at the repo root** — single source of truth for all 8 Python apps.
   - `line-length = 200` (the repository rule, not ruff's default 88), `target-version = "py310"`.
   - `extend-exclude` for `.venv`, `custom-venv`, `node_modules`, `coverage`, `data`.
   - `select = ["E9", "F401", "F841", "F811"]` initially; `ARG` and `B` added in later phases.
   - `per-file-ignores` for `F811` on pytest modules: a test parameter legitimately shadows an imported fixture name (e.g. `navigator` in `apps/scrapper/scrapper/navigator/test/tecnoempleoNavigator_test.py`).
   - `ignore-variadic-names = true` for `flake8-unused-arguments`.
2. **`scripts/lint.sh` and `scripts/lint.bat`** — one entry point for local runs and CI, with Windows parity like `scripts/test.sh` / `scripts/test.bat`. Modes: `python`, `web`, `all`.
3. **TypeScript**
   - `apps/web/tsconfig.app.json`: `types: ["vite/client", "vitest/globals", "@testing-library/jest-dom/vitest", "node"]`. This single line takes the typecheck from **761 errors to 133** — `@testing-library/jest-dom/vitest` (not the package root entry) is what augments vitest's `Assertion` interface, and the root entry augments jest's instead, which is what produced the 387 `toBeInTheDocument` errors.
   - `apps/web/package.json`: add a `typecheck` script.
   - `apps/web/eslint.config.js`: `no-unused-vars` with `argsIgnorePattern: '^_'`; `no-explicit-any` stays an **error in production** and becomes a **warning in test/mocks** (271 of the 315 findings are test-side).
   - `apps/e2e`: minimal ESLint configuration plus the eslint devDependencies.
4. **CI** — a `static-analysis` job added to `.github/workflows/ci.yml` (same file, so `ci-gate` wiring stays simple): ruff via `astral-sh/setup-uv`, `npm run lint` + `npm run typecheck` in `apps/web`, eslint in `apps/e2e`. Wired into `ci-gate`'s `needs` so it becomes a required check.
5. **Optional ergonomics** — `.pre-commit-config.yaml` (ruff + eslint on changed files only) and `.vscode/settings.json` wired to ruff and eslint. No CI impact.

### Phasing (one commit each, every commit green)

| # | Commit | Gate enabled afterwards |
|---|---|---|
| 1 | `ruff.toml` + `scripts/lint.sh` / `.bat`, ruff pinned in CI | report only |
| 2 | Auto-fix: `ruff check --fix` for `F401` + `F841` (135 files, ~292 findings) | ruff clean, full test suite green |
| 3 | Fix the two real `F811` bugs (dead `find_all` stub, duplicate import) | `E9,F401,F841,F811` at zero |
| 4 | TS: `types` fix + the 21 production type errors | `tsc -b` green, `npm run build` works |
| 5 | TS: the 112 test-fixture type errors (mocks missing `deployment`/`created`, mock signature drift) | typecheck gate on |
| 6 | TS: the 30 `no-unused-vars` findings + the `no-explicit-any` policy | `npm run lint` green |
| 7 | `ARG` phase: rename intentionally-unused parameters to `_name`; `# noqa: ARG002` with a reason for overridden/interface methods (renaming changes the public keyword-argument contract) | `ARG` added to `select` |
| 8 | Bugbear `B904` / `B905` / `B008` (~50 findings, real bug classes) | `B` added to `select` |
| 9 | Bugbear follow-up: `B007` / `B011` / `B017` / `B018` / `B027` / `B028` / `B034` (the last 14 findings of the whole bugbear set) | the full bugbear set enforced (`B` selector) |

### Documentation

`AGENTS.md` · `READMEs/README_DEVELOPMENT.md` (new "Static Analysis" section) · root `README.md` · `READMEs/README_GITHUB.md` (CI job and required check) · `READMEs/README_INSTALL.md` (new host tool: ruff) · `apps/<module>/README.md` for each cleaned Python app.

## Outcome

All eight phases landed. The gate is green and enforced by the `static-analysis` CI job.

### What is in force now

| Target | Tool | Rules in force |
|--------|------|----------------|
| Python (`apps/`, `scripts/`) | Ruff 0.17.1, root `ruff.toml` | `E9`, `F401`, `F841`, `F811`, `ARG` and the whole flake8-bugbear set (`B`, 44 rules) |
| Web (`apps/web`) | ESLint 9 flat config + `tsc -b` | 0 errors (304 warnings, non-blocking) |
| E2E (`apps/e2e`) | ESLint 9 flat config (`eslint.config.mjs`) | 0 errors (5 warnings) |

### Findings removed

| Class | Before | After |
|-------|--------|-------|
| `F401` unused imports | 255 | 0 |
| `F841` unused variables | 21 | 0 |
| `F811` dead redefinitions | 167 | 0 |
| `ARG` unused arguments (production) | 32 | 0 |
| `B904` missing `raise ... from` | 16 | 0 |
| `B905` `zip()` without `strict=` | 11 | 0 |
| `B008` call in an argument default | 17 | 0 (FastAPI `Depends`/`Query` allowed) |
| `B007` unused loop variable | 3 | 0 |
| `B011` `assert False` | 1 | 0 |
| `B017` blind `pytest.raises(Exception)` | 4 | 0 |
| `B018` useless expression | 1 | 0 |
| `B027` empty abstract method | 2 | 0 |
| `B028` `warnings.warn` without `stacklevel` | 1 | 0 |
| `B034` positional `re.sub` arguments | 2 | 0 |
| TS type errors (`tsc -b`) | 761 | 0 |
| ESLint errors (`apps/web`) | 395 | 0 |

### Decisions taken along the way

- **Ruff at the repo root**, installed once with `uv tool install ruff`. No app needs it in its own environment.
- **`ARG` is not enforced on pytest modules** (`**/test/**`, `**/tests/**`, `**/*_test.py`, `**/conftest.py`). 356 of the 388 `ARG` findings were pytest fixture parameters: pytest resolves a fixture by the name of the test parameter, so an unused one cannot be renamed to `_name` without breaking fixture resolution. Those parameters exist for the side effect of the fixture, not to be read by the test body. Production code is fully gated.
- **`_name` for intentional non-use, `# noqa: ARG00x - <reason>` for contracts.** The latter is used for the structlog processor signature (`logger`, `method_name`), the markdownify `MarkdownConverter` overrides, the navigator interface (`search`, `check_results`, `fast_forward_page`) and the executor row template method.
- **`B008` is allowed for `fastapi.Depends` / `fastapi.Query`** through `lint.flake8-bugbear.extend-immutable-calls`: declaring an injected dependency or a query parameter in an argument default is the documented FastAPI idiom.
- **The whole bugbear set is enabled with the `B` selector**, not a hand-picked list of rules. The 34 rules that were already clean (`B002`-`B006`, `B009`, `B010`, `B012`-`B016`, `B019`-`B026`, `B029`-`B033`, `B035`, `B039`, `B043`, `B901`, `B903`, `B909`, `B911`, `B912`) cost nothing to enable and close the gap for good. A ruff release that adds a new bugbear rule therefore turns it on automatically; that is the intended trade-off, because ruff is already installed unpinned and a new bugbear rule usually flags a real defect. `BLE001` is not included: it is a preview rule and a different prefix, so `B` does not select it.
- **`BaseExecutor._init_scrapper` and `_preload_action` are `@abstractmethod`.** All six concrete executors already implemented both, so the contract is unchanged for them; the test doubles (`MockBaseExecutor`, `StubKeywordExecutor`) gained the two overrides. A new executor that forgets one now fails at instantiation instead of silently doing nothing.
- **`pytest.raises(Exception)` was narrowed to the real exception type** in four tests: `json.JSONDecodeError`, `mysql.connector.Error` and `VerificationCodeExtractionError` (twice). The gmail test already documented the expected type in a comment; the comment is now the code.
- **The React Compiler hooks rules stay warnings** (`react-hooks/exhaustive-deps`, `react-hooks/immutability`, `react-hooks/set-state-in-effect`). Making them errors would require migrating the components to the React Compiler model, which is out of scope for this plan. `rules-of-hooks` and `refs` remain errors.
- **`apps/e2e/package.json` must not declare `"type": "module"`** — `coverage.config.ts` uses `__dirname`. The ESLint config is `eslint.config.mjs` instead, so the module system of the package stays CommonJS.

### Real defects found by the new gate

- `GET /api/statistics/filter-configs` accepted `include_old_jobs` and silently ignored it (filter configurations have no archived counterpart). The parameter was removed from the backend endpoint and from the frontend call.
- `execute_with_error_handler` carried four parameters (`db`, `page`, `size`, `order`) it never read; they were removed from the helper, its facade and the callers.
- `getEnvMultiline` declared a `default` it never used, and `get_watcher_stats` a `filter_config_service` it never used. Both were removed.
- `zip(columns, row)` silently truncated when the row was shorter than the column list. With `strict=True` it surfaced two test mocks that returned short rows (`filter_configurations_repository_test.py` was missing the `ordering` value, `jobDeleteRepository_test.py` returned 2-value rows against a 3-column table); both mocks were corrected.
- `apps/web` had **761 TypeScript errors** that CI never saw, because the web Dockerfile only runs `npm run dev` and `npm run build` was never part of the pipeline. The typecheck is now a gate.
- `re.sub` takes `count` **before** `flags`, so `re.M` (and `re.I | re.M`) passed positionally became a replacement cap instead of a flag. Two production call sites did that:
  - `commonlib.stringUtil.removeBlanks` capped the blank runs it stripped at 8, so a text with more than 8 separate blank groups came back with the remaining newlines in it.
  - `commonlib.json_helpers.rawToJson` capped its unescape step at 10, so an LLM answer containing more than 10 escaped `&`/`.`/`*`/`-`/`+`/`#` kept its backslashes and the whole parse failed with a `json.JSONDecodeError`.
  Both now pass `flags=` as a keyword argument, and both are covered by a regression test that fails against the old code.

### Files

- New: `ruff.toml`, `scripts/lint.sh`, `scripts/lint.bat`, `apps/e2e/eslint.config.mjs`
- Modified: `.github/workflows/ci.yml` (new `static-analysis` job, wired into `ci-gate`), `apps/web/eslint.config.js`, `apps/web/package.json`, `apps/web/tsconfig.app.json`, `apps/e2e/package.json`, plus the cleaned sources across all 8 Python apps and the frontend.

### Verification

`./scripts/lint.sh all` passes. `./scripts/test.sh` (every module) → 2483 passed / 1 skipped for the 8 Python apps, 137 web test files / 982 tests, 207 e2e tests.

### Not done (deliberately)

- SonarQube stays in reserve (`sonar-quality-gate-setup-changes.patch`).
- The bugbear rules beyond the ones listed above were measured too: the whole `B` set reports 0 findings, so nothing else is pending on that front.

### Follow-up (after the gate landed)

- The stale `scripts/lint_python.patch` (ruff + mypy, with inverted/broken batch logic) was deleted: it was a superseded attempt at the same work and nothing referenced it. The SonarQube patch is kept on purpose, because SonarQube is still a live option.
- Deliverable 5 was built: `.pre-commit-config.yaml` (ruff + ESLint on the changed files only) and the `.vscode/settings.json` wiring, so the same rules that gate CI also run before the commit.