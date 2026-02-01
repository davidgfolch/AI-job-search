#!/bin/bash
cd apps/backend
uv run uvicorn main:app --reload --port ${1:-8000}
cd ../..
