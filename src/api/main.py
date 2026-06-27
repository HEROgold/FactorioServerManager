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
from api.logging_security import configure_secure_logging, scrub_event

logger = getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI()
    app.router.prefix = "/api"

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

    from .routers import dashboard, login, mods, server, user, version  # noqa: PLC0415

    app.include_router(dashboard.router)
    app.include_router(mods.router)
    app.include_router(server.router)
    app.include_router(login.router)
    app.include_router(user.router)
    app.include_router(version.router)

    return app

logger = getLogger(__name__)
logger.addHandler(StreamHandler())

# Keep secrets (session cookies, Factorio tokens, passwords) out of logs.
configure_secure_logging()

sentry_sdk.init(
    dsn="https://b43620319948689547199679efe43956@o4509360059252736.ingest.de.sentry.io/4511185780277328",
    # Do NOT attach request headers/cookies/IPs: they would leak the session
    # cookie and Factorio credentials. scrub_event removes anything sensitive
    # that still slips through.
    send_default_pii=False,
    before_send=scrub_event,
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

def main() -> None:
    """Run the FastAPI application."""
    uvicorn.run(app, host=app_config.host, port=app_config.port)


if __name__ == "__main__":
    main()
