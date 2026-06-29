"""
db/models/ingestion.py

Async ingestion job tracking (§1.2).

IngestionJob    — one row per ingestion task submitted to the RQ worker.
IngestionJobLog — one row per pipeline stage transition (extract→clean→…→index).
                  Also published to Redis Pub/Sub for SSE streaming.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, TenantMixin, _new_uuid


class IngestionJob(Base, TenantMixin):
    __tablename__ = "ingestion_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    source_path_or_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[Optional[str]] = mapped_column(String(50))
    # status: queued | processing | completed | failed | cancelled
    status: Mapped[str] = mapped_column(String(20), default="queued", nullable=False, index=True)
    progress_percent: Mapped[float] = mapped_column(Float, default=0.0)
    chunks_total: Mapped[int] = mapped_column(Integer, default=0)
    chunks_indexed: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    # config: JSON blob with per-job overrides (chunk_size, overlap, embedding_model, parser)
    config: Mapped[Optional[str]] = mapped_column(Text, comment="JSON object")
    submitted_by: Mapped[Optional[str]] = mapped_column(String(36))
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    # blob path where original file was saved (§1.4)
    blob_path: Mapped[Optional[str]] = mapped_column(Text)

    logs: Mapped[list["IngestionJobLog"]] = relationship(
        back_populates="job", cascade="all, delete-orphan", order_by="IngestionJobLog.timestamp"
    )


class IngestionJobLog(Base):
    """One row per stage-transition log line for an IngestionJob."""
    __tablename__ = "ingestion_job_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ingestion_jobs.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    level: Mapped[str] = mapped_column(String(10), default="INFO")
    message: Mapped[str] = mapped_column(Text, nullable=False)

    job: Mapped["IngestionJob"] = relationship(back_populates="logs")
