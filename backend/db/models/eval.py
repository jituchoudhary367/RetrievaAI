"""
db/models/eval.py

Retrieval-quality offline evaluation models (§1.6).

EvalQuery — admin-curated "golden set" of labeled queries.
EvalRun   — one row per periodic eval pass; stores aggregate metrics as JSON.

The Analytics page's Retrieval Performance panel shows the last EvalRun,
labeled with its timestamp.  This is NOT a live metric — it's a real,
standard offline-eval pattern and the UI must say so.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, TenantMixin, _new_uuid


class EvalQuery(Base, TenantMixin):
    """One entry in the labeled ground-truth set."""
    __tablename__ = "eval_queries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    # expected_document_ids: JSON array of document IDs, e.g. '["doc1","doc2"]'
    expected_document_ids: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class EvalRun(Base, TenantMixin):
    """
    Aggregate metrics for one complete replay of all EvalQuery rows.

    metrics: JSON object, e.g.:
      {
        "mrr": 0.72,
        "hit_rate_at_5": 0.85,
        "ndcg_at_10": 0.68,
        "top1_accuracy": 0.60,
        "num_queries": 42
      }
    """
    __tablename__ = "eval_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    metrics: Mapped[Optional[str]] = mapped_column(Text, comment="JSON object")
    # status: running | completed | failed
    status: Mapped[str] = mapped_column(String(20), default="running", nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
