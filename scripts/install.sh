#!/bin/bash
set -e
# debug: show commands
# set -x

# Installs this repo's local development environment:
#   - commonlib first, then every app (Poetry / uv / npm; e2e also gets its Playwright browsers)
#   - the shared host tools: CodeGraph (with agent wiring and the project index), Crawlee, Ruff
#   - the default Ollama model (qwen2.5:3b) on the server the AI modules resolve
#   - data/logs + data/metrics, re-owning folders created by root in the containers
# Host prerequisites (Python, Poetry, uv, npm, Docker) and `.env` / `.env.secrets` are
# not created here: see READMEs/README_INSTALL.md. Optional or remote steps (Ollama pull,
# CodeGraph, Ruff) warn and continue instead of aborting the dependency install.

OLLAMA_CONTAINER=ai-job-search-ollama

ollama_hf_spec() {
    case "$1" in
        qwen2.5:3b) echo "hf.co/Qwen/Qwen2.5-3B-Instruct-GGUF:q4_k_m" ;;
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

# The model is often already on the server -- a remote host on the LAN is shared
# between machines, and a previous run may have pulled it. Check first so a
# blocked registry does not trigger a duplicate HuggingFace download.
ollama_has_model() {
    local model="$1"
    local run; run="$(ollama_runner)"
    if [ -n "$run" ]; then
        # `ollama show` exits non-zero when the model is absent and honours OLLAMA_HOST.
        $run show "$model" >/dev/null 2>&1 && return 0
        return 1
    fi
    local host="${OLLAMA_HOST:-}"
    [ -n "$host" ] || return 1
    # No CLI and no container: ask the remote server directly (404 when absent).
    curl -sf -m 10 -o /dev/null -X POST "$host/api/show" -H "Content-Type: application/json" -d "{\"name\": \"$model\"}" 2>/dev/null
}

ollama_pull() {
    local model="$1"
    if ollama_has_model "$model"; then
        echo "$model already present on the Ollama server (${OLLAMA_HOST:-local}); skipping the download."
        return 0
    fi
    local run; run="$(ollama_runner)"
    if [ -z "$run" ]; then
        # No local CLI and no container: try a remote Ollama host reached over HTTP
        # (e.g. a server on the LAN discovered by commonlib). Pull lands on that host.
        local host; host="${OLLAMA_HOST:-}"
        if [ -n "$host" ]; then
            local hf_spec payload
            if ollama_registry_reachable; then
                payload="{\"name\": \"$model\"}"
            else
                hf_spec="$(ollama_hf_spec "$model")"
                if [ -n "$hf_spec" ]; then
                    echo "Ollama registry unreachable (r2.cloudflarestorage.com blocked) - pulling $model from HuggingFace ($hf_spec) on $host..."
                    payload="{\"name\": \"$hf_spec\"}"
                else
                    payload="{\"name\": \"$model\"}"
                fi
            fi
            echo "Pulling $model via remote Ollama host $host..."
            if curl -s -m 120 -X POST "$host/api/pull" -H "Content-Type: application/json" -d "$payload" >/dev/null 2>&1; then
                if [ -n "${hf_spec:-}" ]; then
                    curl -s -m 120 -X POST "$host/api/cp" -H "Content-Type: application/json" -d "{\"source\": \"$hf_spec\", \"destination\": \"$model\"}" >/dev/null 2>&1 || true
                    curl -s -m 120 -X POST "$host/api/delete" -H "Content-Type: application/json" -d "{\"name\": \"$hf_spec\"}" >/dev/null 2>&1 || true
                fi
                return 0
            fi
            echo "WARNING: could not pull $model from remote Ollama host $host; continuing."
        fi
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
        aiEnrich|backend|aiFormFiller|aiCvMatcher|cron|aiEnrichSkill) return 0 ;;
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
    echo "WARNING: no reachable Ollama server found; the model pull below only warns and is skipped (checked the configured URL, host.docker.internal, localhost, the compose service and the LAN)."
fi

echo ""
echo "Pulling Ollama models..."
# The pull talks to the Ollama server resolved above, which may be another host on
# the LAN, so a failure must not abort the dependency install that follows.
ollama_pull qwen2.5:3b # aiEnrich / aiEnrichSkill default

echo ""
echo "Installing CodeGraph (default code intelligence)..."
echo "  curl -fsSL https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.sh | sh"
if curl -fsSL https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.sh | sh; then
    echo "codegraph installed."
    # The installer links into ~/.local/bin, which this shell may not have on
    # PATH yet, so resolve that link directly before wiring anything.
    codegraph_bin="$(command -v codegraph || true)"
    if [ -z "$codegraph_bin" ] && [ -x "$HOME/.local/bin/codegraph" ]; then
        codegraph_bin="$HOME/.local/bin/codegraph"
    fi
    if [ -n "$codegraph_bin" ]; then
        # --yes: non-interactive (global agent configs, auto-detected agents);
        # --init: build this project's .codegraph/ index in the same step.
        echo "Wiring codegraph into the detected agent(s) and indexing this project..."
        "$codegraph_bin" install --yes --init || echo "WARNING: codegraph agent setup or indexing failed; run 'codegraph install --yes --init' later."
    else
        echo "WARNING: codegraph installed but is not on PATH in this shell. Open a new terminal and run: codegraph install --yes --init"
    fi
else
    echo "WARNING: codegraph install failed; continuing without it. Install manually with: curl -fsSL https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.sh | sh"
fi

echo ""
echo "Installing Crawlee..."
uv tool install "crawlee[all]"

echo ""
echo "Installing Ruff (static analysis)..."
# Single zero-dependency binary for the whole repo; scripts/lint.sh falls back to
# `uvx ruff` when it is not on the PATH, so a failure here is not fatal.
uv tool install ruff || echo "WARNING: ruff install failed; continuing. Install manually with: uv tool install ruff"

for dir in apps/*; do
    name="$(basename "$dir")"
    if [ -d "$dir" ] && [ "$name" != "commonlib" ]; then
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
