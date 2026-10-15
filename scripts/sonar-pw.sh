#!/usr/bin/env bash
# Wrapper: cross-platform Python bootstrap
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
python scripts/sonar-pw.py
