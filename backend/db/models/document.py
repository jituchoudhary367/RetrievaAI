"""
db/models/document.py

Document catalog table — a fast, queryable Postgres summary over Qdrant (§1.3).

This table is written/updated by the ingestion task at indexing time.
Qdrant remains the source of truth for vectors/chunks.
This table is a derived index over Qdrant, rebuildable if it ever drifts.

quality_score is computed at ingestion time (real, deterministic formula):
  Start at 1.0, subtract penalties for:
  - Each extraction warning
  - Average OCR confidence below threshold
  - Fraction of chunks outside [min_chunk_size, max_chunk_size]
  Clamped to [0, 1].
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base, TenantMixin, _new_uuid


class Document(Base, TenantMixin):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    title: Mapped[Optional[str]] = mapped_column(String(512))
    source: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # tags: stored as JSON array string, e.g. '["ml","research"]'
    tags: Mapped[Optional[str]] = mapped_column(Text, comment="JSON array of tag strings")
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    quality_score: Mapped[float] = mapped_column(Float, default=1.0)
    blob_path: Mapped[Optional[str]] = mapped_column(
        Text, comment="Path in blob storage where original file lives (§1.4)"
    )
    ingestion_job_id: Mapped[Optional[str]] = mapped_column(String(36), index=True)
    uploaded_by: Mapped[Optional[str]] = mapped_column(String(36))
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
