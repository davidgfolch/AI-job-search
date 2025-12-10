# Quick Start Commands for Docker Development

## Core Services (Backend + Web + Viewer)
```bash
# Start core services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## With AI Services (AI Enrichment + Ollama)
```bash
# Start with AI services
docker-compose --profile ai-services up -d

# Ollama uses models from your host (defaults to ~/.ollama)
# For Windows, set in .env: OLLAMA_MODELS_PATH=C:/Users/YOUR_USERNAME/.ollama
# No need to pull models again - they're already available!

# Test Ollama connection
curl http://localhost:11434/api/tags
```

## With Scrapper
```bash
# Start scrapper service
docker-compose --profile scrapper up -d scrapper

# Or run scrapper manually (one-time execution)
docker-compose run --rm scrapper
```

## All Services
```bash
# Start everything
docker-compose --profile ai-services --profile scrapper up -d
```

## Service URLs
- **Web (React)**: http://localhost:5173
- **Backend (FastAPI)**: http://localhost:8000/docs
- **Viewer (Streamlit)**: http://localhost:8501
- **MySQL**: localhost:3306
- **Ollama**: http://localhost:11434

## Development Tips
- Code changes are automatically detected (hot-reload enabled)
- Backend: Uvicorn auto-reloads on Python file changes
- Web: Vite HMR refreshes browser on code changes
- Viewer: Streamlit auto-reruns on file changes

## Troubleshooting
```bash
# Rebuild after dependency changes
docker-compose build

# Rebuild specific service
docker-compose build backend

# View service logs
docker-compose logs -f backend

# Restart a service
docker-compose restart backend

# Clean rebuild
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```
