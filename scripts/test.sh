#!/bin/bash
#set -x

# Parse arguments
coverage=0
targets=()
app_args=""

for arg in "$@"; do
    if [ "$arg" == "--coverage" ]; then
        coverage=1
        echo "Coverage enabled"
    elif [ -d "$arg" ]; then
        targets+=("$arg")
    elif [ -d "apps/$arg" ]; then
        targets+=("apps/$arg")
    else
        app_args="$app_args $arg"
    fi
done

run_test() {
    local dir=$1
    echo ""
    echo "Testing $(basename "$dir")..."
    pushd "$dir" > /dev/null
    
    local ret=0
    if [ -f "package.json" ]; then
        if [ $coverage -eq 1 ]; then
            npm test -- run --coverage
            ret=$?
            npx coverage-badges --label "$(basename "$dir")" --source coverage/coverage-summary.json
        else
            npx vitest run
            ret=$?
        fi
    elif [ -f "pyproject.toml" ]; then
        if [ -f "uv.lock" ]; then
            if [ $coverage -eq 1 ]; then
                uv run -m coverage run -m pytest
                ret=$?
                uv run -m coverage report -m
                uv run -m coverage xml
                uv run genbadge coverage -i coverage.xml -o coverage.svg -n "$(basename "$dir")"
            else
                uv run -m pytest
                ret=$?
            fi
        else
            if [ $coverage -eq 1 ]; then
                poetry run coverage run -m pytest
                ret=$?
                poetry run coverage report -m
                poetry run coverage xml
                poetry run genbadge coverage -i coverage.xml -o coverage.svg -n "$(basename "$dir")"
                if [ "$(basename "$dir")" == "scrapper" ]; then
                    poetry run python ../../scripts/coverage/scrapper_coverage_gate.py --xml coverage.xml || ret=1
                fi
            else
                poetry run pytest
                ret=$?
            fi
        fi
    else
        echo "No known project type found in $(basename "$dir")"
        ret=1
    fi
    popd > /dev/null
    return $ret
}

run_e2e_gate() {
    if [ $coverage -eq 0 ]; then
        return 0
    fi
    echo ""
    echo "Gating frontend coverage (web unit + e2e union)..."
    node "$(dirname "$0")/coverage/frontend-coverage-gate.mjs" --min 90
}

if [ ${#targets[@]} -gt 0 ]; then
    tests_failed=0
    for target in "${targets[@]}"; do
        if [ "$target" == "apps/e2e" ] || [ "$target" == "apps\e2e" ]; then
            echo ""
            echo "────────────────────────────────────────────────────────"
            echo "Running E2E tests for apps/e2e..."
            echo "────────────────────────────────────────────────────────"
            pushd apps/e2e > /dev/null
            npm test $app_args
            ret=$?
            popd > /dev/null
            if [ $ret -ne 0 ]; then
                tests_failed=1
            fi
            run_e2e_gate || tests_failed=1
        else
            run_test "$target"
            if [ $? -ne 0 ]; then
                tests_failed=1
            fi
        fi
    done
    if [ $tests_failed -ne 0 ]; then
        exit 1
    fi
else
    # Execute commonlib tests first
    tests_failed=0
    if [ -d "apps/commonlib" ]; then
        run_test "apps/commonlib"
        if [ $? -ne 0 ]; then
            tests_failed=1
        fi
    fi
    # Execute other apps tests
    for dir in apps/*; do
        if [ ! -d "$dir" ]; then
            continue
        fi
        if [ "$(basename "$dir")" == "commonlib" ] || [ "$(basename "$dir")" == "e2e" ]; then
            continue
        fi
        if [ ! -f "$dir/package.json" ] && [ ! -f "$dir/pyproject.toml" ]; then
            echo "Skipping $(basename "$dir") (no package.json or pyproject.toml)"
            continue
        fi
        run_test "$dir"
        if [ $? -ne 0 ]; then
            tests_failed=1
        fi
    done

    if [ $tests_failed -eq 0 ]; then
        echo ""
        echo "────────────────────────────────────────────────────────"
        echo "Unit tests passed. Running E2E tests..."
        echo "────────────────────────────────────────────────────────"
        pushd apps/e2e > /dev/null
        npm test
        ret=$?
        popd > /dev/null
        if [ $ret -ne 0 ]; then
            tests_failed=1
        fi
    else
        echo ""
        echo "Skipping E2E tests because unit tests failed."
    fi
    if [ $tests_failed -eq 0 ]; then
        run_e2e_gate || tests_failed=1
    fi
    
    if [ $tests_failed -ne 0 ]; then
        exit 1
    fi
fi