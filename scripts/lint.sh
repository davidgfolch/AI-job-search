#!/bin/bash
# Static analysis entry point for the whole monorepo.
#
# Usage: ./scripts/lint.sh [python|web|e2e|all]     (default: all)
#
#   python  ruff over apps/ and scripts/ (root ruff.toml)
#   web     eslint + tsc typecheck over apps/web
#   e2e     eslint over apps/e2e
#   all     every check above
#
# Ruff is installed once for the whole repo (`uv tool install ruff`); no app
# needs it in its own environment. RUFF_BIN overrides the binary used.

set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 1

target="all"
if [ $# -gt 0 ]; then
    target="$1"
fi

failed=0

resolve_ruff() {
    if [ -n "${RUFF_BIN:-}" ]; then
        echo "$RUFF_BIN"
        return 0
    fi
    if command -v ruff >/dev/null 2>&1; then
        echo "ruff"
        return 0
    fi
    if command -v uvx >/dev/null 2>&1; then
        echo "uvx ruff"
        return 0
    fi
    if command -v uv >/dev/null 2>&1; then
        echo "uv tool run ruff"
        return 0
    fi
    return 1
}

lint_python() {
    echo ""
    echo "────────────────────────────────────────────────────────"
    echo "Static analysis: Python (ruff)"
    echo "────────────────────────────────────────────────────────"
    local ruff_cmd
    if ! ruff_cmd="$(resolve_ruff)"; then
        echo "ruff not found. Install it with: uv tool install ruff" >&2
        return 1
    fi
    echo "Using: $ruff_cmd"
    $ruff_cmd check apps/ scripts/ --config ruff.toml
    local ret=$?
    if [ $ret -ne 0 ]; then
        echo ""
        echo "ruff reported issues (exit $ret)."
    fi
    return $ret
}

lint_web() {
    echo ""
    echo "────────────────────────────────────────────────────────"
    echo "Static analysis: apps/web (eslint + typecheck)"
    echo "────────────────────────────────────────────────────────"
    pushd apps/web > /dev/null || return 1
    npm run lint
    local ret=$?
    if [ $ret -eq 0 ]; then
        npm run typecheck
        ret=$?
    fi
    popd > /dev/null
    return $ret
}

lint_e2e() {
    echo ""
    echo "────────────────────────────────────────────────────────"
    echo "Static analysis: apps/e2e (eslint)"
    echo "────────────────────────────────────────────────────────"
    pushd apps/e2e > /dev/null || return 1
    npm run lint
    local ret=$?
    popd > /dev/null
    return $ret
}

case "$target" in
    python) lint_python || failed=1 ;;
    web) lint_web || failed=1 ;;
    e2e) lint_e2e || failed=1 ;;
    all)
        lint_python || failed=1
        lint_web || failed=1
        lint_e2e || failed=1
        ;;
    *)
        echo "Unknown target '$target'. Expected: python, web, e2e, all" >&2
        exit 2
        ;;
esac

echo ""
if [ $failed -ne 0 ]; then
    echo "Static analysis FAILED."
    exit 1
fi
echo "Static analysis passed."
exit 0
