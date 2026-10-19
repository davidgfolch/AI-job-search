#!/bin/bash
cd apps/aiFormFiller
uv run uvicorn aiFormFiller.main:app --host 127.0.0.1 --port 8080
cd ../..
