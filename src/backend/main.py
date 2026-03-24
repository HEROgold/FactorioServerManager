"""Main FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api import auth, mods, servers
from backend.config import settings
from backend.rate_limit import RateLimitMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan events."""
    # Startup
    print(f"Starting Factorio Server Manager API on port {settings.PORT}")
    yield
    # Shutdown
    print("Shutting down Factorio Server Manager API")


app = FastAPI(
    title="Factorio Server Manager API",
    description="API for managing Factorio game servers",
    version="2.0.0",
    lifespan=lifespan,
)

# Middleware
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(servers.router, prefix="/api/servers", tags=["servers"])
app.include_router(mods.router, prefix="/api/mods", tags=["mods"])

# Serve React frontend in production
if settings.ENVIRONMENT == "production":
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development",
    )
