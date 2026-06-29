"""
services/health_sampler.py

Periodic HealthSample writer for the Analytics system-health panel.

Launched as a background task from app/main.py lifespan. Samples
system metrics every 60 seconds and writes a HealthSample row.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime, timezone

from app.config import get_settings
from db.engine import async_session_factory
from db.models.health import HealthSample

logger = logging.getLogger(__name__)

_SAMPLE_INTERVAL_SECONDS = 60


async def _measure_redis_latency() -> float | None:
    try:
        import redis as redis_lib  # noqa: PLC0415
        cfg = get_settings()
        client = redis_lib.Redis.from_url(cfg.redis.url, socket_timeout=1.0)
        t = time.monotonic()
        client.ping()
        return (time.monotonic() - t) * 1000
    except Exception:
        return None


async def _measure_qdrant_latency() -> float | None:
    try:
        from qdrant_client import QdrantClient  # noqa: PLC0415
        cfg = get_settings()
        client = QdrantClient(host=cfg.qdrant.host, port=cfg.qdrant.port, timeout=1.0)
        t = time.monotonic()
        client.get_collections()
        return (time.monotonic() - t) * 1000
    except Exception:
        return None


async def _measure_postgres_latency() -> float | None:
    try:
        from sqlalchemy import text  # noqa: PLC0415
        async with async_session_factory() as db:
            t = time.monotonic()
            await db.execute(text("SELECT 1"))
            return (time.monotonic() - t) * 1000
    except Exception:
        return None


async def _get_system_metrics() -> dict:
    try:
        import psutil  # noqa: PLC0415
        return {
            "cpu_percent": psutil.cpu_percent(interval=None),
            "memory_percent": psutil.virtual_memory().percent,
        }
    except ImportError:
        return {}


async def sample_once(tenant_id: str = "00000000-0000-0000-0000-000000000001") -> None:
    """Take one health sample and persist it."""
    redis_ms = await _measure_redis_latency()
    qdrant_ms = await _measure_qdrant_latency()
    postgres_ms = await _measure_postgres_latency()
    sys_metrics = await _get_system_metrics()

    # Determine overall status
    components = []
    for name, latency in [("redis", redis_ms), ("qdrant", qdrant_ms), ("postgres", postgres_ms)]:
        status = "healthy" if latency is not None else "unhealthy"
        components.append({"name": name, "status": status, "latency_ms": latency})

    statuses = {c["status"] for c in components}
    overall = "healthy"
    if "unhealthy" in statuses:
        overall = "unhealthy"
    elif "degraded" in statuses:
        overall = "degraded"

    try:
        async with async_session_factory() as db:
            db.add(HealthSample(
                tenant_id=tenant_id,
                sampled_at=datetime.now(timezone.utc),
                overall_status=overall,
                cpu_percent=sys_metrics.get("cpu_percent"),
                memory_percent=sys_metrics.get("memory_percent"),
                redis_latency_ms=redis_ms,
                qdrant_latency_ms=qdrant_ms,
                postgres_latency_ms=postgres_ms,
                components_json=json.dumps(components),
            ))
            await db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("HealthSampler: write failed: %s", exc)


async def run_health_sampler() -> None:
    """Background loop — samples every SAMPLE_INTERVAL_SECONDS."""
    logger.info("HealthSampler started (interval=%ds).", _SAMPLE_INTERVAL_SECONDS)
    while True:
        try:
            await sample_once()
        except Exception as exc:  # noqa: BLE001
            logger.warning("HealthSampler: sample_once error: %s", exc)
        await asyncio.sleep(_SAMPLE_INTERVAL_SECONDS)


__all__ = ["run_health_sampler", "sample_once"]
