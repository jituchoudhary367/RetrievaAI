"""
db/models/health.py

HealthSample — periodic system health snapshots for the Analytics system-health panel.

Written by services/health_sampler.py on a background schedule.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base, TenantMixin, _new_uuid


class HealthSample(Base, TenantMixin):
    __tablename__ = "health_samples"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    sampled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    # Overall: "healthy" | "degraded" | "unhealthy"
    overall_status: Mapped[str] = mapped_column(String(20), nullable=False)
    cpu_percent: Mapped[Optional[float]] = mapped_column(Float)
    memory_percent: Mapped[Optional[float]] = mapped_column(Float)
    redis_latency_ms: Mapped[Optional[float]] = mapped_column(Float)
    qdrant_latency_ms: Mapped[Optional[float]] = mapped_column(Float)
    postgres_latency_ms: Mapped[Optional[float]] = mapped_column(Float)
    # Component status snapshot as JSON string
    components_json: Mapped[Optional[str]] = mapped_column(
        String(2000), comment="JSON snapshot of ComponentHealth list"
    )
