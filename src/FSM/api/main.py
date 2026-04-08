"""FastAPI application entry for the FSM API."""

from pathlib import Path

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

from fsm.api.config import app_config
from FSM.logging_utils import get_logger

logger = get_logger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
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

    # Mount static files used by some routers
    static_path = Path(__file__).resolve().parents[1] / "static"
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

    # Include routers lazily to avoid import cycles during staged migration.
    try:
        from .routers import dashboard, login, mods, server  # noqa: PLC0415

        app.include_router(dashboard.router)
        app.include_router(mods.router)
        app.include_router(server.router)
        app.include_router(login.router)
    except Exception as err:  # noqa: BLE001 - staged migration import failures handled intentionally
        logger.debug(
            "Router import failed during staged migration; continuing",
            exc_info=err,
        )

    return app


# Initialize Sentry for ASGI (FastAPI) and wrap the app with Sentry middleware.
# We set `send_default_pii=True` to capture basic request user info.
sentry_sdk.init(
    dsn=app_config.sentry_dsn,
    send_default_pii=True,
)

app = create_app()
app = SentryAsgiMiddleware(app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("FSM.api.main:app", host=app_config.host, port=app_config.port, reload=app_config.reload)
