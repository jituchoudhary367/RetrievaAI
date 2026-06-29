"""
app/main.py

FastAPI application factory with full lifespan management.

Lifespan:
  1. Create all DB tables (SQLAlchemy create_all — idempotent)
  2. Run DB seed (default tenant + 3 built-in tools — idempotent)
  3. Launch background health sampler task
  4. Yield (app is live)
  5. Cancel background tasks on shutdown
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.models import ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("Starting RAG API Service (env=%s)...", settings.env)

    # 1 — Create all DB tables (no-op if already exist)
    try:
        from db.base import Base
        import db.models  # noqa: F401 — registers all ORM models
        from db.engine import async_engine
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified/created.")
    except Exception as exc:
        logger.error("DB table creation failed: %s", exc, exc_info=True)

    # 2 — Seed default tenant + tools (idempotent)
    try:
        from db.engine import async_session_factory
        from db.seed import seed_database
        async with async_session_factory() as db:
            await seed_database(db)
    except Exception as exc:
        logger.error("DB seeding failed: %s", exc, exc_info=True)

    # 3 — Start background health sampler
    from services.health_sampler import run_health_sampler
    sampler_task = asyncio.create_task(run_health_sampler(), name="health_sampler")

    yield

    # 4 — Shutdown
    logger.info("Shutting down RAG API Service...")
    sampler_task.cancel()
    try:
        await sampler_task
    except asyncio.CancelledError:
        pass


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="RAG API Service",
        description="Production RAG backend — FastAPI + Qdrant + Postgres + Redis",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── CORS ──────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.security.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Global exception handler ──────────────────────────────────────────
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception: %s", exc, exc_info=True)
        error_response = ErrorResponse(
            status_code=500,
            errors=[ErrorDetail(code="INTERNAL_SERVER_ERROR", message="An unexpected error occurred.")],
        )
        return JSONResponse(status_code=500, content=error_response.model_dump(by_alias=True))

    # ── Routers ───────────────────────────────────────────────────────────
    from routes.health import router as health_router
    from routes.search import router as search_router
    from routes.query import router as query_router
    from routes.ingest import router as legacy_ingest_router  # kept for backward-compat
    from routes.auth import router as auth_router
    from routes.documents import router as documents_router
    from routes.ingestion import router as ingestion_router
    from routes.analytics import router as analytics_router
    from routes.tools import router as tools_router
    from routes.settings import router as settings_router
    from routes.conversations import router as conversations_router
    from routes.notifications import router as notifications_router

    api_prefix = settings.api_v1_prefix  # "/api/v1"
    auth_prefix = "/api"

    # Legacy routes — keep existing prefix conventions
    app.include_router(health_router)
    app.include_router(search_router, prefix=api_prefix)
    app.include_router(query_router, prefix=api_prefix)
    app.include_router(legacy_ingest_router)  # already includes its own /api/v1 prefix

    # New routes — mounted at /api (without versioning for the wired pages)
    app.include_router(auth_router, prefix=auth_prefix)
    app.include_router(documents_router, prefix=auth_prefix)
    app.include_router(ingestion_router, prefix=auth_prefix)
    app.include_router(analytics_router, prefix=auth_prefix)
    app.include_router(tools_router, prefix=auth_prefix)
    app.include_router(settings_router, prefix=auth_prefix)
    app.include_router(conversations_router, prefix=auth_prefix)
    app.include_router(notifications_router, prefix=auth_prefix)

    return app


app = create_app()
