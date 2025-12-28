#!/bin/bash
#set -x

# Parse arguments
coverage=0
for arg in "$@"; do
    if [ "$arg" == "--coverage" ]; then
        coverage=1
        echo "Coverage enabled"
    fi
done

# Execute tests
for dir in packages/* apps/*; do
    if [ ! -d "$dir" ]; then
        continue
    fi
    
    echo ""
    echo "Testing $(basename "$dir")..."
    pushd "$dir" > /dev/null
    
    if [ -f "package.json" ]; then
        if [ $coverage -eq 1 ]; then
            npm test -- run --coverage
            npx coverage-badges
        else
            npm test -- run
        fi
    elif [ -f "pyproject.toml" ]; then
        if [ -f "uv.lock" ]; then
            if [ $coverage -eq 1 ]; then
                uv run -m coverage run -m pytest
                uv run -m coverage report -m
                uv run -m coverage xml
                uv run python -m coverage_badge -o coverage.svg -f
            else
                uv run -m pytest
            fi
        else
            if [ $coverage -eq 1 ]; then
                poetry run coverage run -m pytest
                poetry run coverage report -m
                poetry run coverage xml
                poetry run coverage-badge -o coverage.svg -f
            else
                poetry run pytest
            fi
        fi
    else
        echo "No known project type found in $(basename "$dir")"
    fi
    
    popd > /dev/null
done