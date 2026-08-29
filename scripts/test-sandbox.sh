#!/bin/bash
# Sandboxed docker verification for Dependabot upgrades (dependabot-agent).
# Brings up the affected service(s) in an isolated 'dependabot-test' project so the
# live ai-job-search-* stack and its data are never touched, then checks logs.
# Usage: ./scripts/test-sandbox.sh <service|project> [--profile <name>] [--no-db-clone] [--keep]
set -u

PROJECT="dependabot-test"
FILES="-f docker-compose.yml -f docker-compose.test.override.yml"
SANDBOX_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/.docker-sandbox"
BACKUP_SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/mysql/backup.sh"

TARGET=""
DB_CLONE=1
KEEP=0
PROFILE=""
for arg in "$@"; do
    case "$arg" in
        --no-db-clone) DB_CLONE=0 ;;
        --keep) KEEP=1 ;;
        --profile) PROFILE_ENABLED=1 ;;
        --profile=*) PROFILE="${arg#--profile=}" ;;
        -p) PROFILE_ENABLED=1 ;;
        *) if [ "${PROFILE_ENABLED:-0}" -eq 1 ]; then PROFILE="$arg"; PROFILE_ENABLED=0; else TARGET="$arg"; fi ;;
    esac
done

PROFILE_ARGS=""
if [ -n "$PROFILE" ]; then
    PROFILE_ARGS="--profile $PROFILE"
fi

if [ -z "$TARGET" ]; then
    echo "Usage: $0 <service|project> [--profile <name>] [--no-db-clone] [--keep]" >&2
    exit 1
fi

# Modules disabled in .env (all their *_JOB/*_SKILL/*_ENABLED flags false) get a build-only check.
env_file() { echo "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/.env"; }
module_disabled() {
    local keys=""
    case "$1" in
        aienrich) keys="AI_ENRICH_JOB AI_ENRICH_SKILL" ;;
        aienrichnew) keys="AI_ENRICHNEW_JOB AI_ENRICHNEW_SKILL" ;;
        aienrichskill) keys="AI_ENRICHSKILL_ENABLED" ;;
        aienrich3) keys="AI_ENRICH3_JOB AI_ENRICH3_SKILL" ;;
        aicvmatcher) keys="AI_CVMATCHER_ENABLED" ;;
    esac
    [ -z "$keys" ] && return 1
    if [ -f "$(env_file)" ]; then
        for key in $keys; do
            val=$(grep -E "^${key}=" "$(env_file)" | head -n1 | cut -d= -f2- | tr -d "'\" ")
            case "$val" in
                [Tt]rue|[Yy]es|[Yy]|TRUE|1) return 1 ;;
            esac
        done
    fi
    return 0
}

if module_disabled "$TARGET"; then
    echo "Module '$TARGET' is disabled in .env, performing build-only check..."
    docker compose $FILES $PROFILE_ARGS -p "$PROJECT" build "$TARGET"
    exit $?
fi

cleanup() {
    if [ "$KEEP" -eq 1 ]; then
        echo "Keep mode: leaving sandbox running in project '$PROJECT'."
        return 0
    fi
    echo "Tearing down sandbox project '$PROJECT'..."
    docker compose $FILES $PROFILE_ARGS -p "$PROJECT" rm -sfv > /dev/null 2>&1
    docker volume rm "${PROJECT}_mongo_data_sandbox" > /dev/null 2>&1
    rm -rf "$SANDBOX_DIR"
    echo "Sandbox removed."
}
trap cleanup EXIT

echo "Building and starting '$TARGET' in isolated project '$PROJECT'..."
docker compose $FILES $PROFILE_ARGS -p "$PROJECT" up -d --build "$TARGET"
if [ $? -ne 0 ]; then
    echo "Sandbox build/up failed." >&2
    exit 1
fi

if [ "$DB_CLONE" -eq 1 ] && [ "$TARGET" == "backend" ]; then
    echo "Cloning live MySQL 'jobs' DB into sandbox mysql..."
    "$BACKUP_SCRIPT" || { echo "MySQL backup failed." >&2; exit 1; }
    BACKUP_FILE=$(ls -t "$(dirname "${BASH_SOURCE[0]}")/mysql/backups/"*_backup.sql 2>/dev/null | head -n 1)
    if [ -n "$BACKUP_FILE" ]; then
        echo "Waiting for sandbox mysql to accept authenticated connections..."
        ready=0
        for i in $(seq 1 30); do
            if docker exec -e MYSQL_PWD=rootPass ai-job-search-test-mysql /usr/bin/mysql -h 127.0.0.1 -u root -e "SELECT 1" > /dev/null 2>&1; then ready=1; break; fi
            sleep 2
        done
        if [ "$ready" -ne 1 ]; then
            echo "Sandbox mysql not ready for restore after 30 tries." >&2
            exit 1
        fi
        docker exec -i -e MYSQL_PWD=rootPass ai-job-search-test-mysql /usr/bin/mysql -u root jobs < "$BACKUP_FILE" \
            || { echo "MySQL restore failed." >&2; exit 1; }
    fi
fi

echo "Waiting for sandbox services to become ready..."
docker compose $FILES $PROFILE_ARGS -p "$PROJECT" ps

echo "--- Logs for $TARGET (last 100 lines) ---"
docker compose $FILES $PROFILE_ARGS -p "$PROJECT" logs "$TARGET" --tail=100

echo "Checking sandbox logs for errors..."
if docker compose $FILES $PROFILE_ARGS -p "$PROJECT" logs "$TARGET" 2>&1 | grep -E 'ERROR|CRITICAL|Traceback' > /dev/null; then
    echo "Sandbox log check FAILED: ERROR/CRITICAL/Traceback found in '$TARGET' logs." >&2
    exit 1
fi
