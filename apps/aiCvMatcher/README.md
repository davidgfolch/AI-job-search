# AI CV Matcher

This module handles fast CV matching against job descriptions using local Hugging Face embedding models (`sentence-transformers`). It acts as a dedicated microservice that continuously polls the database for pending CV matches if `AI_CVMATCHER_CVMATCHER_CV_MATCH` is enabled in the environment.

## Requirements

- Python >= 3.10
- MySQL Database (Shared within monorepo)
- `uv` package manager

## Quickstart

Configure `.env` with:
```env
AI_CVMATCHER_CVMATCHER_CV_MATCH=True
AI_CVMATCHER_CVMATCHER_CV_MATCH_NEW_LIMIT=100
```
Then run via Docker:
```bash
docker-compose up -d aicvmatcher
```

Or manually:
```bash
cd apps/aiCvMatcher
uv run aicvmatcher
```
