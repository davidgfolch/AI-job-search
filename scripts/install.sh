#!/bin/bash

echo ""
echo "Installing commonlib library..."
cd packages/commonlib && poetry install && cd ../..

for app in apps/*; do
    echo ""
    echo "Installing $(basename $app)..."
    if [ "$app" == "apps/aiEnrich" ]; then
        cd "$app" && uv tool install --force crewai & cd ../..
    else
        cd "$app" && poetry install & cd ../..
    fi
done
