---
name: graphify-dev
description: "Use for any task that implements, changes, or improves graphify functionality in this repo (HTML visualization, community labeling, edge injection, dependency filtering, or the monorepo pipeline). Mandatory before editing anything graphify-related so the uv-installed graphify package is never modified directly."
---

# graphify development

This skill governs how to change or improve graphify in this repository. It exists because a previous agentic SDLC session tried to modify the graphify package installed by `uv tool` directly, which is never allowed.

## Hard rule: never edit the uv-installed graphify package

graphify runs from a `uv tool` install, NOT from this repo. Its package code lives outside the project:

- Windows: `C:\Users\<user>\AppData\Roaming\uv\tools\graphifyy\Lib\site-packages\graphify\`
- Linux/Mac: `~/.local/share/uv/tools/graphifyy/lib/python*/site-packages/graphify/` (or the path from `uv tool dir`)

Do NOT edit, patch, or add files there. Any change is lost on the next `uv tool upgrade graphifyy` or reinstall, and it silently diverges from the released wheel. All customization is done in this repo instead (see below).

### Verify the install is pristine

Before making graphify changes, confirm no prior session left edits inside the uv package:

```bash
# 1. Find the installed package path
UV_PY=$(uv tool run --from graphifyy python -c "import sys; print(sys.executable)")
GRAPHIFY_DIR=$("$UV_PY" -c "import graphify, os; print(os.path.dirname(graphify.__file__))")

# 2. Diff against the pristine PyPI wheel for the installed version
VERSION=$(graphify --version)
WHEEL_URL=$(curl -s https://pypi.org/pypi/graphifyy/$VERSION/json | python -c "import sys, json; d=json.load(sys.stdin); print([u['url'] for u in d['urls'] if u['filename'].endswith('.whl')][0])")
# download the wheel, unzip to a temp dir, then:
diff -r <pristine>/graphify "$GRAPHIFY_DIR" --exclude=__pycache__
```

If the diff is non-empty, the package was modified. Restore it by reinstalling:
`uv tool install --force graphifyy==<version>` (or `uv tool upgrade graphifyy`). Never try to preserve or re-apply the edits.

## Always invoke through the repo scripts

Agents run graphify in this repo by calling the wrappers — `scripts\graphify\graphify.bat` (Windows) or `scripts/graphify/graphify.sh` (Linux/Mac) — never the raw `graphify` binary. The wrappers own the full pipeline (no args = rebuild, `--clean`, `--module <name>`), delegate read-only/meta subcommands (`query`, `path`, `explain`, `--help`, `--version`) verbatim, and shadow the graph/HTML-mutating subcommands (`update`, `cluster-only`, `add`, `export`, `extract`, `merge-graphs`, URLs) so `graphify-out/graph.html` always keeps the repo customization.

### Hard rule: `graphify-out/graph.html` is repo-owned

`graphify-out/graph.html` is generated ONLY by `scripts/graphify/graphify-html-grouped.py` (module-grouped matrix). NEVER let upstream CLI output replace it:
- Never run `graphify export html`, a bare `graphify update .`, `graphify cluster-only`, or a direct path build — they write the default/aggregated visualization and destroy the custom output.
- Regenerating HTML only (data already in `graphify-out/graph.json`): `python scripts/graphify/graphify-html-grouped.py`.
- Rebuilding data + HTML: the wrapper pipeline (no args) or `--module <name>` — Step 5 already runs the custom generator.
- Mutating wrapper subcommands (`update .`, `cluster-only`, `export html`, …) automatically re-run the custom generator afterwards, restoring the module-grouped HTML.

## Where customization actually lives

All graphify implementation lives in this repo under `scripts/graphify/`:

| File | Purpose |
|------|---------|
| `graphify.bat` / `graphify.sh` | Monorepo pipeline: clean → extract each `apps/*` module (`--no-cluster --code-only`) → `graphify merge-graphs` → post-process → cluster → report → HTML. |
| `graphify-filter-deps.py` | Post-processes `graphify-out/graph.json`: removes external dependency nodes (`pkg_*`/`ref_*` ids, `package.json`/`manifest.json` sources, bare module names). |
| `graphify-inject-edges.py` | Reads `graphify-out/cross-module-edges.json`, adds an INFERRED edge between the highest-degree node of each module pair. |
| `graphify-label-communities.py` | Deterministic (no-LLM) community labeling; writes `graphify-out/.graphify_labels.json`. |
| `graphify-html-grouped.py` | Step 5: generates `graphify-out/graph.html` by filling the template with nodes/edges/modules JSON. |
| `graphify_raw_viz.py` | Builds vis-network datasets from the raw merged graph (`graph.raw.json`, preserved right after `merge-graphs`): nodes colored by module, edges from raw links. Shared `sanitize`/`js_safe` helpers. |
| `templates/graphify-html.tpl` | The HTML/CSS/JS template for the module-grouped matrix visualization. Includes an "Original graph (no postprocessing)" toggle that swaps in the raw datasets and force-directed physics view. |

This repo only uses the graphify CLI (extract/merge/cluster) and Python APIs as-is. Everything custom — module grouping, layering, labels, toggles, zoom behavior — is implemented as post-processing scripts + template, never inside uv.

## How to change or improve graphify

1. **Read the pipeline first.** `scripts/graphify/graphify.sh` (or `.bat`) is the single entry point. Understand which step produces the output you want to change before touching anything.
2. **Changes to the visualization** → edit `scripts/graphify/templates/graphify-html.tpl`, then regenerate with `python scripts/graphify/graphify-html-grouped.py` (fast: it only rebuilds the HTML from the existing `graphify-out/graph.json`). Full pipeline `scripts/graphify/graphify.sh` only needed if graph data itself changed.
3. **Changes to graph data** (nodes/edges/communities) → edit the relevant post-processing script and re-run the full pipeline (or `--module <name>` + merge steps).
4. **Verify by regenerating** `graphify-out/graph.html` and opening it, or inspecting the emitted JSON. Re-run `scripts/graphify/graphify.sh update .` (or `scripts\graphify\graphify.bat update .` on Windows) after any code change to keep `graphify-out/` current (AST-only, no API cost).

### Worked example: a sidebar toggle default

The "Show file nodes" checkbox is defined in `scripts/graphify/templates/graphify-html.tpl` (`<input type="checkbox" id="file-cb" ...>`). Making it checked by default is just adding the `checked` attribute there and re-running `python scripts/graphify/graphify-html-grouped.py`. No uv code involved.

## When NOT to use this skill

- Using graphify to query an existing graph (asking architecture questions, `/graphify query`, `path`, `explain` — all run through `scripts/graphify/graphify.[bat|sh]`) → use the `graphify` skill instead.
- Running a one-off graph build without changing graphify itself → the `graphify` skill.
- Only `graphify-out/*` output files changed and you just want to rebuild → `scripts/graphify/graphify.sh update .` (or `.bat` on Windows).
