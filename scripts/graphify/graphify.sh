#!/bin/bash
# Graphify: build per-module knowledge graphs, merge, inject cross-module edges
#
# Usage:
#   ./scripts/graphify.sh              Full pipeline: clean, extract all, merge, inject, report
#   ./scripts/graphify.sh --clean      Purge old graph data only
#   ./scripts/graphify.sh --module X   Re-extract a single module, then merge + inject + report
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
# graphify honors a GRAPHIFY_OUT env var; drop any inherited value so
# per-module extractions write to apps/<module>/graphify-out, not the root.
unset GRAPHIFY_OUT
GRAPHIFY_OUT="$ROOT_DIR/graphify-out"
EDGES_FILE="$GRAPHIFY_OUT/cross-module-edges.json"

# Production modules (e2e excluded)
MODULES=(
    commonlib backend web scrapper
    aiEnrich aiEnrichNew aiEnrich3 aiEnrichSkill
    aiCvMatcher aiFormFiller cron
)

# ────────────────────── Parse arguments ─────────────────────
clean=0
single_module=""

for arg in "$@"; do
    case "$arg" in
        --clean)
            clean=1
            ;;
        --module)
            # next arg is the module name
            ;;
        --module=*)
            single_module="${arg#--module=}"
            ;;
        *)
            # Check if previous arg was --module
            if [ "$prev_arg" = "--module" ]; then
                single_module="$arg"
            fi
            ;;
    esac
    prev_arg="$arg"
done

# ────────────────────── Clean function ──────────────────────
clean_graph() {
    echo "Cleaning graphify-out/..."
    if [ -d "$GRAPHIFY_OUT" ]; then
        # Preserve cross-module-edges.json
        if [ -f "$EDGES_FILE" ]; then
            cp "$EDGES_FILE" /tmp/cross-module-edges-backup.json
        fi
        rm -rf "$GRAPHIFY_OUT"
        mkdir -p "$GRAPHIFY_OUT"
        if [ -f /tmp/cross-module-edges-backup.json ]; then
            mv /tmp/cross-module-edges-backup.json "$EDGES_FILE"
        fi
        echo "  Cleaned. (cross-module-edges.json preserved)"
    else
        mkdir -p "$GRAPHIFY_OUT"
        echo "  Created graphify-out/"
    fi
    # Clean per-module extraction outputs
    for module in "${MODULES[@]}"; do
        if [ -d "$ROOT_DIR/apps/$module/graphify-out" ]; then
            rm -rf "$ROOT_DIR/apps/$module/graphify-out"
        fi
    done
    echo "  Cleaned per-module graphify-out/ directories"
}

# ────────────────────── Extract function ────────────────────
extract_module() {
    local module=$1
    local dir="$ROOT_DIR/apps/$module"
    if [ ! -d "$dir" ]; then
        echo "  SKIP: apps/$module does not exist"
        return 0
    fi
    echo ""
    echo "Extracting $module..."
    if graphify extract "$dir" --no-cluster --code-only 2>&1; then
        echo "  OK: $module"
    else
        echo "  WARN: $module extraction failed (continuing)"
    fi
}

# ────────────────────── Main pipeline ───────────────────────

if [ $clean -eq 1 ]; then
    clean_graph
    echo ""
    echo "Clean complete."
    exit 0
fi

if [ -n "$single_module" ]; then
    echo "Re-extracting module: $single_module"
    extract_module "$single_module"
    echo ""
    echo "Merging graphs..."
else
    # Full pipeline
    clean_graph

    echo ""
    echo "Extracting modules..."
    # commonlib first (dependency for all others)
    extract_module "commonlib"
    # remaining modules
    for module in "${MODULES[@]}"; do
        if [ "$module" = "commonlib" ]; then
            continue
        fi
        extract_module "$module"
    done

    echo ""
    echo "Merging graphs..."
fi

# Collect all module graph.json files
GRAPH_FILES=()
for module in "${MODULES[@]}"; do
    gfile="$ROOT_DIR/apps/$module/graphify-out/graph.json"
    if [ -f "$gfile" ]; then
        GRAPH_FILES+=("$gfile")
    fi
done

if [ ${#GRAPH_FILES[@]} -lt 2 ]; then
    echo "ERROR: Need at least 2 module graphs to merge (found ${#GRAPH_FILES[@]})"
    echo "Available:"
    for module in "${MODULES[@]}"; do
        gfile="$ROOT_DIR/apps/$module/graphify-out/graph.json"
        if [ -f "$gfile" ]; then
            echo "  $module"
        fi
    done
    exit 1
fi

graphify merge-graphs "${GRAPH_FILES[@]}" --out "$GRAPHIFY_OUT/graph.json"

echo ""
echo "Filtering external dependency nodes..."
python "$SCRIPT_DIR/graphify-filter-deps.py"

echo ""
echo "Injecting cross-module edges..."
python "$SCRIPT_DIR/graphify-inject-edges.py"

echo ""
echo "Step 1 — Assigning communities..."
graphify cluster-only "$ROOT_DIR" 2>/dev/null || echo "  WARN: cluster-only failed, graph.json is still valid"

echo ""
echo "Step 2 — Labeling communities..."
python "$SCRIPT_DIR/graphify-label-communities.py"

echo ""
echo "Step 3 — Finalizing report (Leiden clustering is non-deterministic, may shift communities)..."
graphify cluster-only "$ROOT_DIR" 2>/dev/null || echo "  WARN: cluster-only failed, but .graphify_labels.json was written"

echo ""
echo "Step 4 — Re-labeling to capture any shifted communities..."
python "$SCRIPT_DIR/graphify-label-communities.py" 2>/dev/null

echo ""
echo "Step 5 — Generating module-grouped graph.html..."
python "$SCRIPT_DIR/graphify-html-grouped.py"

echo ""
echo "────────────────────────────────────────────────────────"
echo "Graph complete. Outputs in $GRAPHIFY_OUT/"
echo ""
echo "  graph.html          - interactive graph grouped by module, open in browser"
echo "  GRAPH_REPORT.md     - architecture audit report"
echo "  graph.json          - raw graph data"
echo "  cross-module-edges.json - edge definitions (editable)"
echo "────────────────────────────────────────────────────────"
