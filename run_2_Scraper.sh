#!/bin/bash
.venv/bin/python3 -V
.venv/bin/python3 src/ai_job_search/scrappers.py "$@"
