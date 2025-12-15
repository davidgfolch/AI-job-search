#!/bin/bash
cd apps/backend
uv run uvicorn main:app --reload --port 8000
cd ../..
