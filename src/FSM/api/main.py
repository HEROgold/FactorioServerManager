from pathlib import Path
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

def create_app() -> FastAPI:
    app = FastAPI()
    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount static and templates are used by routers directly (templates dir path shown below)
    static_path = Path(__file__).resolve().parents[1] / "static"
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

    # include routers lazily to avoid import cycles
    try:
        from .routers import dashboard, mods

        app.include_router(dashboard.router)
        app.include_router(mods.router)
    except Exception:
        # allow import failures during staged migration
        pass

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.FSM.api.main:app", host="0.0.0.0", port=8000, reload=True)
