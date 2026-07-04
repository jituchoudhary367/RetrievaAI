"""
db/models/audit.py

AuditLogEntry and Notification ORM models (§1.9).

AuditLogEntry — written by every admin-level mutation (invite sent,
                setting changed, API key generated, document deleted, etc.)
Notification  — written when an ingestion job completes/fails, an invite
                is accepted, or an eval run finishes.  Polled, not pushed.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base, _new_uuid


class AuditLogEntry(Base):
    __tablename__ = "audit_log_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    actor_user_id: Mapped[Optional[str]] = mapped_column(String(36), index=True)
    # action: e.g. "document.delete", "setting.update", "api_key.create"
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # target: human-readable description of what was acted upon
    target: Mapped[Optional[str]] = mapped_column(Text)
    # extra context as a JSON string (e.g. the setting key that changed)
    detail: Mapped[Optional[str]] = mapped_column(Text, comment="JSON blob")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    # type: "ingestion_complete" | "ingestion_failed" | "invite_accepted" | "eval_complete"
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
