#!/bin/bash

echo ""
echo "Testing commonlib library..."
cd packages/commonlib && poetry run pytest && cd ../..

for app in apps/*; do
    echo ""
    echo "Installing $(basename $app)..."
    if [ "$app" == "apps/aiEnrich" ]; then
        cd "$app" && UV_PROJECT_ENVIRONMENT=custom-venv uv sync && uv run pytest & cd ../..
    else
        cd "$app" && poetry run pytest & cd ../..
    fi
done
