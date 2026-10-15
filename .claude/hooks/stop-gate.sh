#!/usr/bin/env bash
set -uo pipefail
ROOT="${1:-$(pwd)}"
cd "$ROOT" || exit 0
MODIFIED_SRC="$(git status --porcelain 2>/dev/null | grep -E '\.py$' | sed 's/^...//' || true)"
if [ -n "$MODIFIED_SRC" ]; then
    echo '{"continue":true,"stopReason":"SDLC gate: Python source files were modified. Before finishing, run scripts/test.sh (Unix) or scripts/test.bat (Windows), then scripts/sonar.sh scan (or .bat). Do not push until tests and SonarQube quality gate pass."}'
else
    echo '{"continue":true}'
fi
exit 0
