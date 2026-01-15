#!/bin/bash
#set -x

# Parse arguments
coverage=0
target=""
for arg in "$@"; do
    if [ "$arg" == "--coverage" ]; then
        coverage=1
        echo "Coverage enabled"
    elif [ -d "$arg" ]; then
        target="$arg"
    fi
done

run_test() {
    local dir=$1
    echo ""
    echo "Testing $(basename "$dir")..."
    pushd "$dir" > /dev/null
    
    if [ -f "package.json" ]; then
        if [ $coverage -eq 1 ]; then
            npm test -- run --coverage
            npx coverage-badges --label "$(basename "$dir")"
        else
            npx vitest run
        fi
    elif [ -f "pyproject.toml" ]; then
        if [ -f "uv.lock" ]; then
            if [ $coverage -eq 1 ]; then
                uv run -m coverage run -m pytest
                uv run -m coverage report -m
                uv run -m coverage xml
                uv run genbadge coverage -i coverage.xml -o coverage.svg -n "$(basename "$dir")"
            else
                uv run -m pytest
            fi
        else
            if [ $coverage -eq 1 ]; then
                poetry run coverage run -m pytest
                poetry run coverage report -m
                poetry run coverage xml
                poetry run genbadge coverage -i coverage.xml -o coverage.svg -n "$(basename "$dir")"
            else
                poetry run pytest
            fi
        fi
    else
        echo "No known project type found in $(basename "$dir")"
    fi
    popd > /dev/null
}

if [ -n "$target" ]; then
    run_test "$target"
else
    # Execute commonlib tests first
    if [ -d "apps/commonlib" ]; then
        run_test "apps/commonlib"
    fi
    # Execute other apps tests
    for dir in apps/*; do
        if [ ! -d "$dir" ]; then
            continue
        fi
        if [ "$(basename "$dir")" == "commonlib" ]; then
            continue
        fi
        run_test "$dir"
    done
fi