#!/bin/bash
#set -x

# Parse arguments
coverage=0
target=""
app_args=""

for arg in "$@"; do
    if [ "$arg" == "--coverage" ]; then
        coverage=1
        echo "Coverage enabled"
    elif [ -d "$arg" ]; then
        target="$arg"
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
            npx coverage-badges --label "$(basename "$dir")"
            ret=$?
        else
            npx vitest run
            ret=$?
        fi
    elif [ -f "pyproject.toml" ]; then
        if [ -f "uv.lock" ]; then
            if [ $coverage -eq 1 ]; then
                uv run -m coverage run -m pytest
                uv run -m coverage report -m
                uv run -m coverage xml
                uv run genbadge coverage -i coverage.xml -o coverage.svg -n "$(basename "$dir")"
                ret=$?
            else
                uv run -m pytest
                ret=$?
            fi
        else
            if [ $coverage -eq 1 ]; then
                poetry run coverage run -m pytest
                poetry run coverage report -m
                poetry run coverage xml
                poetry run genbadge coverage -i coverage.xml -o coverage.svg -n "$(basename "$dir")"
                ret=$?
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

if [ -n "$target" ]; then
    if [ "$target" == "apps/e2e" ] || [ "$target" == "apps\e2e" ]; then
        echo ""
        echo "────────────────────────────────────────────────────────"
        echo "Running E2E tests for apps/e2e..."
        echo "────────────────────────────────────────────────────────"
        if [ -f "apps/backend/uv.lock" ]; then
            uv run --project apps/backend python scripts/run_e2e_tests.py $app_args
        else
            python scripts/run_e2e_tests.py $app_args
        fi
        if [ $? -ne 0 ]; then
             exit 1
        fi
    else
        run_test "$target"
    fi
else
    # Execute commonlib tests first
    if [ -d "apps/commonlib" ]; then
        run_test "apps/commonlib"
    fi
    # Execute other apps tests
    tests_failed=0
    for dir in apps/*; do
        if [ ! -d "$dir" ]; then
            continue
        fi
        if [ "$(basename "$dir")" == "commonlib" ] || [ "$(basename "$dir")" == "e2e" ]; then
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
        if [ -f "apps/backend/uv.lock" ]; then
            uv run --project apps/backend python scripts/run_e2e_tests.py
        else
            python scripts/run_e2e_tests.py
        fi
        if [ $? -ne 0 ]; then
            tests_failed=1
        fi
    else
        echo ""
        echo "Skipping E2E tests because unit tests failed."
    fi
    
    if [ $tests_failed -ne 0 ]; then
        exit 1
    fi
fi