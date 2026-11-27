#!/bin/bash
# Dump the local 'jobs' DB and full-restore it onto the other machine.
# Default (no params) auto-discovers the target MySQL IP on the LAN.
# Usage:
#   ./sync.sh                  # auto-discover target
#   ./sync.sh 192.168.1.50     # explicit target IP
#   ./sync.sh --dry-run        # show summary, skip restore
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT="$( cd "$DIR/../.." && pwd )"
cd "$ROOT/apps/commonlib" || exit 1
poetry run python -m commonlib.sync.mysql_sync "$@"
