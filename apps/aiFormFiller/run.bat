@echo off
cd /d "%~dp0"
uv run uvicorn aiFormFiller.main:app --host 127.0.0.1 --port 8080
