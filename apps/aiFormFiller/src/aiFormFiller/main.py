from importlib.metadata import version as _v
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from commonlib.terminalColor import cyan
from .api.routes import router, init_routes
from .context_loader import ContextLoader
from . import config as cfg


def create_app(context_loader: ContextLoader | None = None) -> FastAPI:
    app = FastAPI(title="AI Form Filler", version=_v("aiFormFiller"))
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    if context_loader is None:
        cv_path = cfg.get_cv_path()
        lf_path = cfg.get_looking_for_path()
        context_loader = ContextLoader(cv_path, lf_path)
        context_loader.load()
    init_routes(context_loader)
    app.include_router(router)
    return app


def run():
    import uvicorn
    port = cfg.get_port()
    print(cyan(f"AI Form Filler v{_v('aiFormFiller')}"))
    print(cyan(f"Starting on http://127.0.0.1:{port}"))
    uvicorn.run("aiFormFiller.main:app", host="0.0.0.0", port=port, reload=False)


app = create_app()
