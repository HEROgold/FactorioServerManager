"""FastAPI application entry for the fsm API."""
from logging import getLogger
from pathlib import Path

import sentry_sdk
import uvicorn.config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from herogold.log import StreamHandler

from api.config import app_config

logger = getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI()
    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    app.add_middleware(
        CORSMiddleware,  # ty:ignore[invalid-argument-type]
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

logger = getLogger(__name__)
logger.addHandler(StreamHandler())

sentry_sdk.init(
    dsn="https://b43620319948689547199679efe43956@o4509360059252736.ingest.de.sentry.io/4511185780277328",
    # Add data like request headers and IP for users, if applicable;
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for tracing.
    traces_sample_rate=1.0,
    # To collect profiles for all profile sessions,
    # set `profile_session_sample_rate` to 1.0.
    profile_session_sample_rate=1.0,
    # Profiles will be automatically collected while
    # there is an active span.
    profile_lifecycle="trace",
    environment=app_config.environment,
)

app = create_app()

@app.get("/sentry-debug")
async def trigger_error() -> float:
    return 1 / 0

def main() -> None:
    uvicorn.run(app, host=app_config.host, port=app_config.port)


if __name__ == "__main__":
    main()
