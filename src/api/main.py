"""FastAPI application entry for the fsm API."""
import secrets
import socket
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from logging import getLogger
from os import environ
from pathlib import Path

import sentry_sdk
import uvicorn.config
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from herogold.log import StreamHandler

from api.config import app_config, session_config
from api.deps import CSRF_COOKIE_NAME, CSRF_HEADER_NAME
from api.logging_security import configure_secure_logging, scrub_event

logger = getLogger(__name__)

# HTTP methods that cannot change server state and so are exempt from CSRF checks.
_CSRF_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})

# Auth endpoints authenticate by credentials, not the session cookie, so they are
# not CSRF targets and must stay reachable even when the browser still holds a
# stale session cookie from a prior login/deploy. Paths include the "/api" router
# prefix (see create_app).
_CSRF_EXEMPT_PATHS = frozenset({"/api/login", "/api/logout"})

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

    @app.middleware("http")
    async def _csrf_protect(request: Request, call_next):  # noqa: ANN202, ANN001
        """Enforce double-submit CSRF on cookie-authenticated state changes.

        The auth paths in ``_CSRF_EXEMPT_PATHS`` are skipped outright: they
        authenticate by credentials rather than the session cookie, and gating
        on cookie presence alone would wrongly block a fresh login whenever a
        stale ``fsm_session`` cookie lingers in the browser. Every other unsafe
        method is checked only when a session cookie is present: the
        ``X-CSRF-Token`` header must match the ``fsm_csrf`` cookie; a browser on
        another origin can send the cookie but cannot read it to populate the
        header, which is what defeats the forgery.
        """
        if (
            request.method not in _CSRF_SAFE_METHODS
            and request.url.path not in _CSRF_EXEMPT_PATHS
            and request.cookies.get(session_config.cookie_name)
        ):
            cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
            header_token = request.headers.get(CSRF_HEADER_NAME)
            if not cookie_token or not header_token or not secrets.compare_digest(
                cookie_token,
                header_token,
            ):
                return JSONResponse(
                    {"detail": "CSRF validation failed"},
                    status_code=status.HTTP_403_FORBIDDEN,
                )
        return await call_next(request)

    # Mount static files used by some routers
    static_path = Path(__file__).resolve().parents[1] / "static"
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

    from .routers import dashboard, feature_flags, login, mods, server, user, version  # noqa: PLC0415

    app.include_router(dashboard.router)
    app.include_router(feature_flags.router)
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

# DSN comes from the environment (or api_config.ini), never hardcoded in source.
# When unset, Sentry stays disabled instead of shipping events to a baked-in key.
# Require a real http(s) URL so neither an empty value nor confkit's placeholder
# default ("sentry_dsn") is ever passed to sentry_sdk.
_sentry_dsn = (environ.get("SENTRY_DSN") or app_config.sentry_dsn or "").strip().strip('"').rstrip(",").strip('"')
if _sentry_dsn.startswith(("http://", "https://")):
    sentry_sdk.init(
        dsn=_sentry_dsn,
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
