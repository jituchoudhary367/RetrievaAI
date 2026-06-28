import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.models import ErrorResponse, ErrorDetail
from routes.health import router as health_router
from routes.search import router as search_router
from routes.query import router as query_router

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("Starting RAG API Service...")
    logger.info(f"Environment: {settings.env}")
    yield
    logger.info("Shutting down RAG API Service...")

def create_app() -> FastAPI:
    settings = get_settings()
    
    app = FastAPI(
        title="RAG API Service",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.security.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global Exception Handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        error_detail = ErrorDetail(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred."
        )
        error_response = ErrorResponse(
            status_code=500,
            errors=[error_detail]
        )
        return JSONResponse(
            status_code=500,
            content=error_response.model_dump(by_alias=True)
        )

    # Include routers
    app.include_router(health_router)  # Mounted at root: /health, /ready, /live
    app.include_router(search_router, prefix=settings.api_v1_prefix)
    app.include_router(query_router, prefix=settings.api_v1_prefix)

    return app

app = create_app()
