@echo off
cd /d "%~dp0..\.."
uv run cron
cd /d "%~dp0..\.."
