#!/bin/bash
set -e
# debug: show commands
# set -x

echo ""
echo "Installing graphify..."
uv tool install graphifyy
uv tool install "graphifyy[ollama]"
uv tool install "graphifyy[openai]"
uv tool install "graphifyy[sql]"
ollama pull qwen2.5-coder:7b
graphify install --project --platform opencode
graphify . --backend ollama
git add .opencode/ AGENTS.md


echo ""
echo "Installing commonlib..."
(cd apps/commonlib && poetry lock && poetry install)

for dir in apps/*; do
    if [ -d "$dir" ] && [ "$(basename "$dir")" != "commonlib" ]; then
        if [ ! -f "$dir/package.json" ] && [ ! -f "$dir/pyproject.toml" ]; then
            echo "Skipping $(basename "$dir") (no package.json or pyproject.toml)"
            continue
        fi
        echo ""
        echo "Installing $(basename "$dir")..."
        if [ -f "$dir/package.json" ]; then
            (cd "$dir" && npm install)
        elif [ "$(basename "$dir")" == "aiEnrich" ] || [ "$(basename "$dir")" == "aiEnrichNew" ] || [ "$(basename "$dir")" == "aiEnrich3" ] || [ "$(basename "$dir")" == "backend" ] || [ "$(basename "$dir")" == "aiFormFiller" ] || [ "$(basename "$dir")" == "aiCvMatcher" ] || [ "$(basename "$dir")" == "cron" ]; then
            (cd "$dir" && uv sync)
        else
            (cd "$dir" && poetry lock && poetry install)
        fi
    fi
done
