#!/bin/bash
.venv/bin/python3 -V
.venv/bin/python3 src/ai_job_search/scrapper_main.py "$@"

# If you want to run without .venv activated, use:
# PYTHONPATH=src .venv/bin/python3 -m ai_job_search.scrapper_main "$@"
# or on Windows PowerShell:
#  .\.venv\Scripts\python -m ai_job_search.scrapper_main "$@"
