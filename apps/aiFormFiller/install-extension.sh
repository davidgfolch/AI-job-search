#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
export LOG_CONSOLE_MODE=message
uv run python scripts/install_extension.py "$@"
