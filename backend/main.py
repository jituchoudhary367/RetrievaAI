"""
main.py

FastAPI application assembler.

Responsibilities:
  - Configure root logger
  - Mount all API routers
  - Configure CORS middleware
  - Provide a global exception handler for uncaught errors
"""

from __future__ import annotations

import logging
import sys

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from routes import query_router, ingest_router, health_router

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
def _configure_logging(log_level: str) -> None:
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )

# ---------------------------------------------------------------------------
# App Factory
# ---------------------------------------------------------------------------
def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    settings = get_settings()
    _configure_logging(settings.log_level)

    app = FastAPI(
        title="Production RAG Service",
        description="Scalable Retrieval-Augmented Generation API",
        version="1.0.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount routers
    app.include_router(query_router)
    app.include_router(ingest_router)
    app.include_router(health_router)

    # Global Exception Handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger = logging.getLogger("main")
        logger.error("Unhandled exception: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": str(exc) if settings.debug else "An unexpected error occurred.",
            },
        )

    return app

# Expose app for Uvicorn
app = create_app()
