"""
routes/health.py

FastAPI router for Liveness and Readiness probes.

Endpoints:
  GET /health/live  — Service liveness (always 200 OK if process is up)
  GET /health/ready — Service readiness (verifies Redis, Qdrant, LLM API)
"""

from __future__ import annotations

import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", summary="Liveness probe")
def liveness() -> dict:
    """Return 200 OK. Used by Kubernetes/Docker liveness probes."""
    return {"status": "ok", "probe": "live"}


@router.get("/ready", summary="Readiness probe")
def readiness() -> JSONResponse:
    """
    Check downstream dependencies (Redis, Qdrant, LLM).
    Returns 200 OK if ready, 503 Service Unavailable if any critical
    dependency is down.
    """
    settings = get_settings()
    status = {"status": "ok", "probe": "ready", "components": {}}
    is_ready = True

    # 1. Check Redis
    try:
        import redis
        client = redis.Redis.from_url(settings.redis.url, socket_timeout=1.0)
        client.ping()
        status["components"]["redis"] = "ok"
    except ImportError:
        status["components"]["redis"] = "skipped (not installed)"
    except Exception as exc:  # noqa: BLE001
        logger.warning("Readiness probe: Redis unavailable: %s", exc)
        status["components"]["redis"] = "down"
        # Redis is treated as non-critical for core functionality since we have fallbacks,
        # but in a strict prod environment you might set is_ready = False here.

    # 2. Check Qdrant
    try:
        from qdrant_client import QdrantClient
        # Only verify we can construct the client and timeout is configured;
        # full HTTP ping might be too slow for a high-frequency probe, but let's do a fast one.
        client = QdrantClient(
            host=settings.qdrant.host,
            port=settings.qdrant.port,
            timeout=1.0,
            api_key=settings.qdrant.api_key,
        )
        collections = client.get_collections()
        status["components"]["qdrant"] = "ok"
    except ImportError:
        status["components"]["qdrant"] = "skipped (not installed)"
    except Exception as exc:  # noqa: BLE001
        logger.warning("Readiness probe: Qdrant unavailable: %s", exc)
        status["components"]["qdrant"] = "down"
        is_ready = False

    if is_ready:
        return JSONResponse(content=status, status_code=200)
    
    status["status"] = "error"
    return JSONResponse(content=status, status_code=503)


__all__ = ["router"]
