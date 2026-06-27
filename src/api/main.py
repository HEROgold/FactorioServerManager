"""FastAPI application entry for the fsm API."""
import socket
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from logging import getLogger
from os import environ
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

# When running locally the backend binds a random free port (see main()). It
# publishes that port here so the Bun dev server can proxy /api to the live
# backend. Written while the server is up, removed on shutdown — never stale.
PORT_FILE = Path(__file__).resolve().parents[2] / ".fsm-backend-port"


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Publish the bound port for the dev proxy while the server is alive."""
    port = getattr(app.state, "bound_port", None)
    if port is not None:
        PORT_FILE.write_text(str(port))
    try:
        yield
    finally:
        PORT_FILE.unlink(missing_ok=True)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(lifespan=_lifespan)
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

def _free_port(host: str) -> int:
    """Ask the OS for an unused port so local runs never collide on 8000."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind((host, 0))
        return probe.getsockname()[1]


def main() -> None:
    """Run the FastAPI application on a free port, published for the dev proxy."""
    host = app_config.host
    # Drop any port file left behind by an unclean exit so readers never see a
    # stale port before the lifespan publishes the fresh one.
    PORT_FILE.unlink(missing_ok=True)
    # FSM_PORT pins the port (CI / scripts); otherwise grab a random free one.
    port = int(environ["FSM_PORT"]) if environ.get("FSM_PORT") else _free_port(host)
    app.state.bound_port = port
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
