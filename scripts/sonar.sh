#!/usr/bin/env bash
# ===== AI Job Search SonarQube Analysis Script (Linux/Mac) =====
# Usage: ./scripts/sonar.sh <command> [token]
#   ./scripts/sonar.sh up        - Start SonarQube via Docker
#   ./scripts/sonar.sh scan      - Run tests + coverage + SonarQube analysis
#   ./scripts/sonar.sh up-scan   - Start SonarQube, wait for ready, then scan
#   ./scripts/sonar.sh down      - Stop SonarQube
# Token: passed as 2nd arg, set SONAR_TOKEN env var, or loaded from .env.secrets.

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

bash scripts/bootstrap-env.sh 2>/dev/null || true

CMD="${1:-}"
TOKEN="${2:-${SONAR_TOKEN:-}}"

if [ -z "$TOKEN" ] && [ -f .env.secrets ]; then
    TOKEN=$(grep '^SONAR_TOKEN=' .env.secrets | head -1 | cut -d= -f2- || true)
fi

if [ -z "$CMD" ]; then
    echo "Usage: ./scripts/sonar.sh <command> [token]"
    echo "Commands: up | scan | up-scan | down"
    exit 1
fi

COMPOSE=(-f docker-compose.yml -f docker/docker-compose.sonarqube.yml)

case "$CMD" in
    up)
        echo "Starting SonarQube..."
        docker compose "${COMPOSE[@]}" up -d sonarqube
        echo
        echo "SonarQube starting at $(grep '^SONAR_HOST_URL=' .env.secrets 2>/dev/null | head -1 | cut -d= -f2- || echo http://localhost:9000) (default http://localhost:9000)"
        echo "Waiting for server to be ready..."
        until curl -sf http://localhost:9000/api/system/status >/dev/null 2>&1; do
            sleep 5
        done
        echo "SonarQube is ready."
        bash scripts/sonar-pw.sh
        ;;
    scan)
        if [ -z "$TOKEN" ]; then
            echo "Error: no token. Run ./scripts/sonar.sh up first, or pass a token."
            exit 1
        fi
        echo "Running tests with coverage..."
        bash scripts/test.sh --coverage
        echo
        echo "Running SonarQube analysis..."
        docker compose "${COMPOSE[@]}" run --rm sonar-scanner
        python scripts/sonar-marker.py
        echo
        echo "SonarQube Quality Gate wait completed."
        ;;
    up-scan)
        echo "Starting SonarQube..."
        docker compose "${COMPOSE[@]}" up -d sonarqube
        echo "Waiting for SonarQube to be ready..."
        until curl -sf http://localhost:9000/api/system/status >/dev/null 2>&1; do
            sleep 5
        done
        echo "SonarQube is ready."
        bash scripts/sonar-pw.sh
        if [ -z "$TOKEN" ] && [ -f .env.secrets ]; then
            TOKEN=$(grep '^SONAR_TOKEN=' .env.secrets | head -1 | cut -d= -f2- || true)
        fi
        if [ -z "$TOKEN" ]; then
            echo "Error: no token. Pass it as an argument or set SONAR_TOKEN."
            exit 1
        fi
        echo "Running tests with coverage..."
        bash scripts/test.sh --coverage
        echo
        echo "Running SonarQube analysis..."
        docker compose "${COMPOSE[@]}" run --rm sonar-scanner
        python scripts/sonar-marker.py
        ;;
    down)
        echo "Stopping SonarQube..."
        docker compose "${COMPOSE[@]}" down
        ;;
    *)
        echo "Unknown command: $CMD"
        echo "Usage: ./scripts/sonar.sh <up|scan|up-scan|down> [token]"
        exit 1
        ;;
esac

echo
echo "SonarQube operation complete."
