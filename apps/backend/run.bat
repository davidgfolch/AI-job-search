cd apps/backend
set PORT=8000
if not "%1"=="" set PORT=%1
uv run uvicorn main:app --reload --port %PORT%
cd ../..