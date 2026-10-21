import os
import uvicorn
from api.main import app  # noqa: F401 - the ASGI app must stay importable as "main:app" for uvicorn

if __name__ == "__main__":
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, reload=True)
