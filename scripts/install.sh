#!/bin/bash
set -x
echo ""
echo "Installing commonlib library..."
cd packages/commonlib && poetry lock && poetry install
cd ../..

for app in ./apps/*/; do
    echo ""
    echo "Installing $(basename $app)..."
    if [ "$app" == "./apps/aiEnrich/" ]; then
        cd "$app" && uv sync && uv tool install --force crewai
    else
        cd "$app" && poetry lock && poetry install
    fi
    cd ../..
done
