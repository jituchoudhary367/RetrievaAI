"""
routes/__init__.py

Flat export surface for FastAPI routers.
"""

from routes.query import router as query_router
from routes.ingest import router as ingest_router
from routes.health import router as health_router

__all__ = ["query_router", "ingest_router", "health_router"]
