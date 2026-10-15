#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
git config core.hooksPath "$ROOT/.githooks"
chmod +x .githooks/pre-push
echo "Git hooks enabled: core.hooksPath=$ROOT/.githooks"
