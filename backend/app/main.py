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
import time
import warnings
from contextlib import asynccontextmanager

warnings.filterwarnings("ignore", category=SyntaxWarning)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from app.config import get_settings
from app.models import ErrorDetail, ErrorResponse, PermissionErrorAlias
from security.auth import AuthError, _decode_token
from services.auth_service import AuthServiceError, EmailNotVerifiedError

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("Starting RAG API Service (env=%s)...", settings.environment)

    # 1 — Create all DB tables (no-op if already exist)
    try:
        from db.base import Base
        import db.models  # noqa: F401 — registers all ORM models
        from db.engine import async_engine
        print("DATABASE URL IS:", settings.database.url)
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

    # 3 — Start background tasks
    from services.health_sampler import run_health_sampler
    sampler_task = asyncio.create_task(run_health_sampler(), name="health_sampler")

    from services.connector_scheduler import run_connector_scheduler
    connector_scheduler_task = asyncio.create_task(run_connector_scheduler(), name="connector_scheduler")


    yield

    # 4 — Shutdown
    logger.info("Shutting down RAG API Service...")
    sampler_task.cancel()
    connector_scheduler_task.cancel()
    for task in [sampler_task, connector_scheduler_task]:
        try:
            await task
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

    from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
    
    # ── Proxy Headers ─────────────────────────────────────────────────────
    # Required for Authlib to verify the callback URL scheme (https) properly
    # when hosted behind a reverse proxy like Render.
    # pyrefly: ignore [bad-argument-type]
    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])

    # ── CORS ──────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.security.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.add_middleware(
        SessionMiddleware, 
        secret_key=settings.security.jwt_secret_key,
        same_site="lax",
        https_only=settings.environment == "production"
    )

    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                payload = _decode_token(token)
                request.state.user_id = payload.get("sub")
            except Exception:
                pass
        return await call_next(request)

    # ── Global exception handler ──────────────────────────────────────────
    def _cors_headers(request: Request) -> dict:
        """Return CORS headers matching the request origin."""
        origin = request.headers.get("origin", "")
        allowed = settings.security.allowed_origins
        allow_origin = origin if ("*" in allowed or origin in allowed) else (allowed[0] if allowed else "*")
        return {
            "Access-Control-Allow-Origin": allow_origin,
            "Access-Control-Allow-Credentials": "true",
        }

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception: %s", exc, exc_info=True)
        error_response = ErrorResponse(
            status_code=500,
            errors=[ErrorDetail(code="INTERNAL_SERVER_ERROR", message="An unexpected error occurred.")],
        )
        return JSONResponse(status_code=500, content=error_response.model_dump(by_alias=True, mode="json"), headers=_cors_headers(request))

    @app.exception_handler(AuthError)
    async def auth_error_handler(request: Request, exc: AuthError):
        error_response = ErrorResponse(
            status_code=exc.status_code,
            errors=[ErrorDetail(code="UNAUTHORIZED", message=exc.detail)],
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.model_dump(by_alias=True, mode="json"),
            headers={**exc.headers, **_cors_headers(request)}
        )


    @app.exception_handler(AuthServiceError)
    async def auth_service_error_handler(request: Request, exc: AuthServiceError):
        error_response = ErrorResponse(
            status_code=exc.status_code,
            errors=[ErrorDetail(code="UNAUTHORIZED", message=exc.detail)],
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.model_dump(by_alias=True, mode="json"),
            headers=exc.headers
        )

    @app.exception_handler(EmailNotVerifiedError)
    async def email_not_verified_error_handler(request: Request, exc: EmailNotVerifiedError):
        error_response = ErrorResponse(
            status_code=403,
            errors=[ErrorDetail(code="EMAIL_NOT_VERIFIED", message=exc.detail)],
        )
        return JSONResponse(
            status_code=403,
            content=error_response.model_dump(by_alias=True, mode="json"),
            headers=exc.headers
        )

    @app.exception_handler(PermissionErrorAlias)
    async def permission_error_handler(request: Request, exc: PermissionErrorAlias):
        error_response = ErrorResponse(
            status_code=403,
            errors=[ErrorDetail(code="FORBIDDEN", message=str(exc))],
        )
        return JSONResponse(
            status_code=403,
            content=error_response.model_dump(by_alias=True, mode="json"),
        )

    @app.get("/", include_in_schema=False)
    async def root():
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/docs")

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        from fastapi.responses import Response
        return Response(status_code=204)

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
    from routes.oauth import router as oauth_router

    api_prefix = settings.api_v1_prefix  # "/api/v1"
    auth_prefix = "/api"

    # Mount all functional routes under /api for consistency with frontend
    app.include_router(health_router, prefix=auth_prefix)
    app.include_router(search_router, prefix=auth_prefix)
    app.include_router(query_router, prefix=auth_prefix)
    app.include_router(legacy_ingest_router, prefix=auth_prefix)

    # New routes — mounted at /api
    app.include_router(auth_router, prefix=auth_prefix)
    app.include_router(oauth_router, prefix=auth_prefix + "/oauth")
    app.include_router(documents_router, prefix=auth_prefix)
    app.include_router(ingestion_router, prefix=auth_prefix)
    app.include_router(analytics_router, prefix=auth_prefix)
    app.include_router(tools_router, prefix=auth_prefix)
    app.include_router(settings_router, prefix=auth_prefix)
    app.include_router(conversations_router, prefix=auth_prefix)
    app.include_router(notifications_router, prefix=auth_prefix)

    from routes.connectors import router as connectors_router
    app.include_router(connectors_router, prefix=auth_prefix)


    return app


app = create_app()
