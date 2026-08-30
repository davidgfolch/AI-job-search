---
name: version-bumper
description: Bump the version of any apps/* module following semver, including syncing dependency references and secondary version files.
---
# Version Bumper Instructions

Use this skill after making changes to any module under `apps/`. Follow these steps to bump the version.

## 1. Detect Modified Apps

Run `git diff --name-only` or check staged files to identify which `apps/*` modules were changed.

## 2. Ask User for Bump Type

For each modified app, ask the user: `major`, `minor`, or `patch`?
- **major**: breaking change (x.0.0)
- **minor**: new feature (0.x.0)
- **patch**: bug fix (0.0.x)

## 3. Update the Version File

Parse the current version and apply the semver bump, then write it back.

### Python apps (pyproject.toml):
```
[project]
version = "x.y.z"
```
Also update `commonlib`'s `__version__` in `commonlib/__init__.py` if modifying commonlib.

### npm apps (web, e2e — package.json):
```json
"version": "x.y.z"
```

### aiFormFiller extension (extension/manifest.json):
```json
"version": "x.y.z"
```

## 4. Sync commonlib Dependency Version

When `commonlib` version is bumped, update the `commonlib==OLD_VERSION` to `commonlib==NEW_VERSION` in ALL apps that depend on it:

| App | File |
|-----|------|
| backend | `apps/backend/pyproject.toml` |
| scrapper | `apps/scrapper/pyproject.toml` |
| aiEnrich | `apps/aiEnrich/pyproject.toml` |
| aiEnrich3 | `apps/aiEnrich3/pyproject.toml` |
| aiEnrichNew | `apps/aiEnrichNew/pyproject.toml` |
| aiCvMatcher | `apps/aiCvMatcher/pyproject.toml` |
| aiFormFiller | `apps/aiFormFiller/pyproject.toml` |

Search for the pattern `commonlib==<old_version>` and replace with `commonlib==<new_version>`.

## 5. Version Reference Table

| App | Primary version file | Extra sync file | Package name (for `importlib.metadata`) |
|-----|---------------------|-----------------|----------------------------------------|
| commonlib | `pyproject.toml` | `commonlib/__init__.py` (`__version__`) | `commonlib` |
| backend | `pyproject.toml` | — | `api` |
| scrapper | `pyproject.toml` | — | `scrapper` |
| aiEnrich | `pyproject.toml` | — | `aiEnrich` |
| aiEnrich3 | `pyproject.toml` | — | `aiEnrich3` |
| aiEnrichNew | `pyproject.toml` | — | `aiEnrichNew` |
| aiCvMatcher | `pyproject.toml` | — | `aiCvMatcher` |
| aiFormFiller | `pyproject.toml` | `extension/manifest.json` | `aiFormFiller` |
| web | `package.json` | — | (npm, no importlib) |
| e2e | `package.json` | — | (npm, no importlib) |

## 6. Verify

Run the affected app's tests afterward:
```bash
# Python (uv)
uv run pytest

# Python (poetry — commonlib, scrapper)
poetry run pytest

# npm
npm test
```

## Usage
- Use this skill after modifying any `apps/*` module to bump its version before committing.
- Always ask the user which bump type (major/minor/patch) — never guess.
