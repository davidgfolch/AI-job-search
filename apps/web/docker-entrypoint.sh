#!/bin/sh
set -e

# Reinstalls node_modules when package-lock.json changes.
# The container keeps dependencies in a persistent Docker volume, so a plain
# image rebuild leaves stale packages behind. This compares the lockfile hash
# against a marker stored inside node_modules and runs `npm ci` only on mismatch.

if [ -f package-lock.json ]; then
    lock_hash=$(sha256sum package-lock.json | awk '{print $1}')
    marker="node_modules/.package-lock.sha256"
    if [ ! -f "$marker" ] || [ "$(cat "$marker")" != "$lock_hash" ]; then
        echo "[web-entrypoint] Dependencies changed or node_modules missing. Running npm ci..."
        npm ci
        echo "$lock_hash" > "$marker"
        echo "[web-entrypoint] npm ci complete."
    else
        echo "[web-entrypoint] node_modules up to date."
    fi
fi

exec "$@"
