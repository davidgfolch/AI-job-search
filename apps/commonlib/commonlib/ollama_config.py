"""Centralized Ollama configuration constants.

Single source of truth for the Ollama server URLs used across all modules.
Runtime override is done via the dedicated env var per module (e.g.
`AI_ENRICH_OLLAMA_BASE_URL`), whose default falls back to these constants.
"""
OLLAMA_DEFAULT_BASE_URL = "http://localhost:11434"
OLLAMA_DOCKER_BASE_URL = "http://ollama:11434"