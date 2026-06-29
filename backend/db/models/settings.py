"""
db/models/settings.py

RuntimeSetting — dynamic, tenant-scoped settings persisted in Postgres (§1.7).

Covers everything in the Settings page that genuinely has no existing
per-tenant override mechanism: max_tokens, timeout, max_file_size,
chunk_size, overlap, embedding_model, vector_db selection, backup_frequency,
retention, cache_ttl, max_concurrent_jobs, memory_limit, etc.

Rate Limit and Concurrent Requests are NOT here — they're in TenantConfig.

value is stored as a JSON string so it can hold any scalar or object.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base, _new_uuid


class RuntimeSetting(Base):
    __tablename__ = "runtime_settings"
    __table_args__ = (
        UniqueConstraint("tenant_id", "key", name="uq_runtime_settings_tenant_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False, comment="JSON value")
    updated_by: Mapped[Optional[str]] = mapped_column(String(36))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class UserPreference(Base):
    """User-scoped preferences (e.g., notification settings) — same pattern as RuntimeSetting."""
    __tablename__ = "user_preferences"
    __table_args__ = (
        UniqueConstraint("user_id", "key", name="uq_user_preferences_user_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False, comment="JSON value")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
