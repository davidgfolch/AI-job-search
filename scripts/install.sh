#!/bin/bash
set -e

for dir in packages/* apps/*; do
    if [ -d "$dir" ]; then
        echo ""
        echo "Installing $(basename "$dir")..."
        if [ -f "$dir/package.json" ]; then
            (cd "$dir" && npm install)
        elif [ "$(basename "$dir")" == "aiEnrich" ]; then
            (cd "$dir" && uv sync && uv tool install --force crewai)
        else
            (cd "$dir" && poetry lock && poetry install)
        fi
    fi
done
