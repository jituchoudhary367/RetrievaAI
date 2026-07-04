"""
routes/analytics.py

Analytics dashboard endpoints.

Queries the telemetry and document tables to provide aggregate metrics
for the frontend dashboards.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from db.engine import get_db
from db.models.telemetry import QueryEvent, SearchEvent
from db.models.document import Document
from db.models.health import HealthSample
from db.models.user import User
from security.auth import get_current_user, require_role
from services.eval_service import get_latest_eval_run

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["analytics"])


class OverviewStats(BaseModel):
    total_queries: int
    active_users: int
    avg_latency_ms: float
    documents_indexed: int
    total_chunks: int

@router.get("/overview", response_model=OverviewStats)
async def get_overview(
    days: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OverviewStats:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    # Total queries
    q_count = await db.execute(
        select(func.count()).select_from(QueryEvent)
        .where(QueryEvent.created_at >= cutoff, QueryEvent.user_id == current_user.id)
    )
    total_queries = q_count.scalar_one()

    # Active users
    u_count = await db.execute(
        select(func.count(func.distinct(QueryEvent.user_id)))
        .where(QueryEvent.created_at >= cutoff, QueryEvent.user_id == current_user.id)
    )
    active_users = u_count.scalar_one()

    # Avg latency
    lat_avg = await db.execute(
        select(func.avg(QueryEvent.total_latency_ms))
        .where(QueryEvent.created_at >= cutoff, QueryEvent.user_id == current_user.id)
    )
    avg_lat = lat_avg.scalar_one() or 0.0

    # Documents & Chunks
    doc_stats = await db.execute(
        select(func.count(), func.sum(Document.chunk_count))
        .select_from(Document)
        .where(Document.user_id == current_user.id)
    )
    docs_idx, chunks_tot = doc_stats.one()

    return OverviewStats(
        total_queries=total_queries,
        active_users=active_users,
        avg_latency_ms=round(avg_lat, 2),
        documents_indexed=docs_idx or 0,
        total_chunks=chunks_tot or 0,
    )

@router.get("/query-distribution")
async def get_query_distribution(
    days: int = Query(default=30),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    # Daily query counts
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(
            func.date_trunc('day', QueryEvent.created_at).label("day"),
            func.count().label("count")
        )
        .where(QueryEvent.created_at >= cutoff, QueryEvent.user_id == current_user.id)
        .group_by(text("day"))
        .order_by(text("day"))
    )
    
    return [{"date": row.day.isoformat() if row.day else None, "count": row.count} for row in result.all()]

@router.get("/top-queries")
async def get_top_queries(
    limit: int = Query(default=10),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    # Simply latest queries for now, could aggregate by similar text
    result = await db.execute(
        select(QueryEvent.query_text, QueryEvent.created_at, QueryEvent.intent)
        .where(QueryEvent.user_id == current_user.id)
        .order_by(QueryEvent.created_at.desc())
        .limit(limit)
    )
    return [{"query": row.query_text, "intent": row.intent, "timestamp": row.created_at.isoformat()} for row in result.all()]

@router.get("/retrieval-quality")
async def get_retrieval_quality(
    current_user: User = Depends(require_role("TENANT_ADMIN", "admin")),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    run = await get_latest_eval_run(db)
    if not run or not run.metrics:
        return {"status": "no_data"}
    
    import json
    metrics = json.loads(run.metrics)
    return {
        "status": run.status,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "metrics": metrics
    }

@router.get("/system-health")
async def get_system_health(
    limit: int = Query(default=60), # Last 60 samples (e.g. 1 hour if 1 min interval)
    current_user: User = Depends(require_role("TENANT_ADMIN", "admin")),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    result = await db.execute(
        select(HealthSample)
        .order_by(HealthSample.sampled_at.desc())
        .limit(limit)
    )
    samples = result.scalars().all()
    # Return chronologically
    return [
        {
            "sampled_at": s.sampled_at.isoformat(),
            "overall_status": s.overall_status,
            "cpu_percent": s.cpu_percent,
            "memory_percent": s.memory_percent,
            "redis_latency_ms": s.redis_latency_ms,
            "qdrant_latency_ms": s.qdrant_latency_ms,
            "postgres_latency_ms": s.postgres_latency_ms,
        }
        for s in reversed(samples)
    ]
