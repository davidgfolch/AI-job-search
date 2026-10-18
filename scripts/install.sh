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

ollama_container_running() {
    docker inspect --format '{{.State.Running}}' "$OLLAMA_CONTAINER" 2>/dev/null | grep -q "true"
}

ollama_host_name() {
    printf '%s' "${OLLAMA_HOST:-}" | sed -E 's#^[^:]+://##; s#/.*##; s#:[0-9]+$##'
}

# The AI modules already know how to find their server (configured URL ->
# host.docker.internal -> localhost -> the compose service -> LAN scan). Ask that
# chain instead of guessing, so the models land on the host that will serve them.
# An OLLAMA_HOST already set in the shell is offered as the primary candidate.
ollama_resolve_url() {
    (cd apps/commonlib && LOG_LEVEL=50 poetry run python - <<'PY' 2>/dev/null | sed -n 's/^OLLAMA_URL=//p' | tail -n 1
import os
from commonlib.ollama_client import resolve_ollama_url
from commonlib.ollama_config import get_configured_ollama_url
print("OLLAMA_URL=" + (resolve_ollama_url(os.environ.get("OLLAMA_HOST") or get_configured_ollama_url()) or ""))
PY
    ) || true
}

ollama_runner() {
    if [ "$(ollama_host_name)" = "ollama" ] && ollama_container_running; then
        echo "docker exec $OLLAMA_CONTAINER ollama"  # the compose name only resolves inside its network
    elif command -v ollama >/dev/null 2>&1; then
        echo "ollama"  # the local CLI honours OLLAMA_HOST, including a server on the LAN
    elif ollama_container_running; then
        echo "docker exec $OLLAMA_CONTAINER ollama"
    else
        echo ""
    fi
}

ollama_unreachable() {
    echo "WARNING: could not pull $1 from the Ollama server (${OLLAMA_HOST:-no server resolved}); continuing. Retry later with: OLLAMA_HOST=<url> ollama pull $1"
    return 0
}

ollama_pull() {
    local model="$1"
    local run; run="$(ollama_runner)"
    if [ -z "$run" ]; then
        echo "WARNING: no Ollama server reachable and no local 'ollama' CLI installed. Pull $model on the server that runs it: ollama pull $model."
        return 0
    fi
    if ollama_registry_reachable; then
        echo "Pulling $model via $run..."
        $run pull "$model" || ollama_unreachable "$model"
    else
        local hf_spec; hf_spec="$(ollama_hf_spec "$model")"
        if [ -n "$hf_spec" ]; then
            echo "Ollama registry unreachable (r2.cloudflarestorage.com blocked) - pulling $model from HuggingFace ($hf_spec)..."
            if $run pull "$hf_spec"; then
                $run cp "$hf_spec" "$model"
                $run rm "$hf_spec"
            fi
        else
            echo "Pulling $model via $run..."
            $run pull "$model" || ollama_unreachable "$model"
        fi
    fi
}

is_uv_app() {
    case "$(basename "$1")" in
        aiEnrich|aiEnrichNew|aiEnrich3|backend|aiFormFiller|aiCvMatcher|cron|aiEnrichSkill) return 0 ;;
    esac
    return 1
}

echo ""
echo "Installing commonlib..."
(cd apps/commonlib && poetry lock && poetry install)

echo ""
echo "Resolving the Ollama server..."
OLLAMA_URL="$(ollama_resolve_url)"
if [ -n "$OLLAMA_URL" ]; then
    export OLLAMA_HOST="$OLLAMA_URL"
    echo "Ollama server: $OLLAMA_URL"
else
    echo "WARNING: no reachable Ollama server found; the model pulls and the graphify indexing below only warn and are skipped (checked the configured URL, host.docker.internal, localhost, the compose service and the LAN)."
fi

echo ""
echo "Installing graphify..."
uv tool install graphifyy
uv tool install "graphifyy[ollama]"
uv tool install "graphifyy[openai]"
uv tool install "graphifyy[sql]"
ollama_pull qwen2.5-coder:7b  # graphify community naming backend
ollama_pull qwen2.5:3b # aiEnrich / aiEnrichSkill default
# The graphify steps talk to the Ollama server resolved above, which may be another
# host on the LAN, so a failure must not abort the dependency install that follows.
graphify install --project --platform opencode || echo "WARNING: graphify project setup failed; continuing without it."
graphify . --backend ollama || echo "WARNING: graphify indexing skipped (the Ollama server was unreachable); run 'graphify . --backend ollama' later."
git add .claude/ .opencode/ AGENTS.md

echo ""
echo "Installing Crawlee..."
uv tool install "crawlee[all]"

for dir in apps/*; do
    name="$(basename "$dir")"
    if [ -d "$dir" ] && [ "$name" != "commonlib" ] && [ "$name" != "graphify-out" ]; then
        if [ ! -f "$dir/package.json" ] && [ ! -f "$dir/pyproject.toml" ]; then
            echo "Skipping $name (no package.json or pyproject.toml)"
            continue
        fi
        echo ""
        echo "Installing $name..."
        if [ -f "$dir/package.json" ]; then
            (cd "$dir" && npm install)
            # The e2e module uses Playwright: install its browser binaries and OS deps.
            if [ "$name" == "e2e" ]; then
                (cd "$dir" && npx playwright install)
                if command -v sudo >/dev/null 2>&1; then
                    (cd "$dir" && sudo npx playwright install-deps) || echo "WARNING: 'sudo npx playwright install-deps' failed; run it manually for e2e browsers."
                else
                    echo "WARNING: sudo not available; run 'sudo npx playwright install-deps' manually for e2e browsers."
                fi
            fi
        elif is_uv_app "$dir"; then
            (cd "$dir" && uv sync)
        else
            (cd "$dir" && poetry lock && poetry install)
        fi
    fi
done

echo ""
echo "Setting up data folder permissions..."
mkdir -p data/logs data/metrics
for dir in apps/*/data; do
    [ -d "$dir" ] && mkdir -p "$dir/logs" "$dir/metrics"
done
owner="$(id -u):$(id -g)"
if find data apps/*/data -not -user "$(id -un)" -print -quit 2>/dev/null | grep -q .; then
    # Containers run as root and create root-owned logs/metrics in these bind mounts,
    # which locks the host user out of its own data/ folders.
    if command -v sudo >/dev/null 2>&1; then
        sudo chown -R "$owner" data apps/*/data || echo "WARNING: chown failed; run: sudo chown -R $owner data apps/*/data"
    else
        echo "WARNING: root-owned files in data/ folders. Run: sudo chown -R $owner data apps/*/data"
    fi
fi
