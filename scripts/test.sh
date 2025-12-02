#!/bin/bash

echo ""
echo "Testing commonlib library..."
cd packages/commonlib && poetry run pytest && cd ../..

# Parse arguments
coverage=0
for arg in "$@"; do
    if [ "$arg" == "--coverage" ]; then
        coverage=1
    fi
done

for app in apps/*; do
    echo ""
    echo "Testing $(basename $app)..."
    if [ -f "$app/package.json" ]; then
        if [ $coverage -eq 1 ]; then
            cd "$app" && npm test -- run --coverage && npx coverage-badges & cd ../..
        else
            cd "$app" && npm test -- run & cd ../..
        fi
    elif [ -f "$app/pyproject.toml" ]; then
        if [ "$app" == "apps/aiEnrich" ]; then
            cd "$app" && UV_PROJECT_ENVIRONMENT=custom-venv uv sync && uv run pytest & cd ../..
        else
            if [ $coverage -eq 1 ]; then
                cd "$app" && poetry run pytest --cov=. --cov-report=xml && poetry run coverage-badge -o coverage.svg -f & cd ../..
            else
                cd "$app" && poetry run pytest & cd ../..
            fi
        fi
    else
        echo "No known project type found in $app"
    fi
done
