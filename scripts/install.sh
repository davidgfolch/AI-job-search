#!/bin/bash
set -e
# debug: show commands
# set -x

echo ""
echo "Installing commonlib..."
(cd apps/commonlib && poetry lock && poetry install)

for dir in apps/*; do
    if [ -d "$dir" ] && [ "$(basename "$dir")" != "commonlib" ]; then
        echo ""
        echo "Installing $(basename "$dir")..."
        if [ -f "$dir/package.json" ]; then
            (cd "$dir" && npm install)
        elif [ "$(basename "$dir")" == "aiEnrich" ]; then
            (cd "$dir" && uv sync && uv tool install --force crewai)
        elif [ "$(basename "$dir")" == "aiEnrichNew" ]; then
            (cd "$dir" && uv sync)
        elif [ "$(basename "$dir")" == "backend" ]; then
            (cd "$dir" && uv sync)
        else
            (cd "$dir" && poetry lock && poetry install)
        fi
    fi
done
