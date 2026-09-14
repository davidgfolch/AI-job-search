#!/bin/bash
set -e
# debug: show commands
# set -x

OLLAMA_CONTAINER=ai-job-search-ollama

ollama_hf_spec() {
    case "$1" in
        qwen2.5:3b) echo "hf.co/Qwen/Qwen2.5-3B-Instruct-GGUF:q4_k_m" ;;
        qwen2.5-coder:7b) echo "hf.co/bartowski/Qwen2.5-Coder-7B-Instruct-GGUF:Q4_K_M" ;;
        *) echo "" ;;
    esac
}

ollama_registry_reachable() {
    [ "${OLLAMA_PULL_SOURCE:-auto}" = "ollama" ] && return 0
    [ "${OLLAMA_PULL_SOURCE:-auto}" = "hf" ] && return 1
    curl -s -m 5 -o /dev/null https://r2.cloudflarestorage.com/ 2>/dev/null
}

ollama_runner() {
    if docker inspect --format '{{.State.Running}}' "$OLLAMA_CONTAINER" 2>/dev/null | grep -q "true"; then
        echo "docker exec $OLLAMA_CONTAINER ollama"
    elif command -v ollama >/dev/null 2>&1; then
        echo "ollama"
    else
        echo ""
    fi
}

ollama_pull() {
    local model="$1"
    local run; run="$(ollama_runner)"
    if [ -z "$run" ]; then
        echo "WARNING: Ollama not found. Pull $model manually (host: ollama pull $model | dockerized: docker exec $OLLAMA_CONTAINER ollama pull $model)."
        return 0
    fi
    if ollama_registry_reachable; then
        echo "Pulling $model via $run..."
        $run pull "$model"
    else
        local hf_spec; hf_spec="$(ollama_hf_spec "$model")"
        if [ -n "$hf_spec" ]; then
            echo "Ollama registry unreachable (r2.cloudflarestorage.com blocked) - pulling $model from HuggingFace ($hf_spec)..."
            if $run pull "$hf_spec"; then
                $run cp "$hf_spec" "$model"
            fi
        else
            echo "Pulling $model via $run..."
            $run pull "$model"
        fi
    fi
}

echo ""
echo "Installing graphify..."
uv tool install graphifyy
uv tool install "graphifyy[ollama]"
uv tool install "graphifyy[openai]"
uv tool install "graphifyy[sql]"
ollama_pull qwen2.5-coder:7b  # graphify community naming backend
ollama_pull qwen2.5:3b # aiEnrich / aiEnrichSkill default
graphify install --project --platform opencode
graphify . --backend ollama
git add .claude/ .opencode/ AGENTS.md


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
