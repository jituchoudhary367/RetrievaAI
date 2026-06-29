"""
db/models/tenant.py

Tenant and TenantConfig ORM models.

Tenant  — one row per organization (multi-tenancy).
TenantConfig — per-tenant overrides for rate limits, concurrent requests, and
               other settings that the wiring prompt explicitly assigns to
               TenantConfig (not RuntimeSetting) per §1.7.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base, TimestampMixin, _new_uuid


class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    plan: Mapped[str] = mapped_column(String(50), default="free")


class TenantConfig(Base, TimestampMixin):
    """Per-tenant operational overrides (rate limits, concurrency)."""
    __tablename__ = "tenant_configs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    rate_limit_requests_per_minute: Mapped[Optional[int]] = mapped_column(Integer)
    max_concurrent_requests: Mapped[Optional[int]] = mapped_column(Integer)
    allowed_models: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="JSON array of allowed model names; null = use global allowlist"
    )
    max_tokens_override: Mapped[Optional[int]] = mapped_column(Integer)
    notes: Mapped[Optional[str]] = mapped_column(Text)
