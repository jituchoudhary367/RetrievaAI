"""
db/models/tool.py

Tool registry and execution log (§1.5).

Tool          — seeded with 3 real tools on startup; metadata-only for new tools.
ToolExecution — one row per real invocation from agents/crag.py or tools/*.py.
                Drives usage counts, sparklines, success rate, recent executions.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, TenantMixin, _new_uuid


class Tool(Base, TenantMixin):
    __tablename__ = "tools"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    # status: active | inactive | metadata_only
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    # is_executable: True for the 3 built-in tools; False for metadata-only registered ones
    is_executable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    executions: Mapped[list["ToolExecution"]] = relationship(
        back_populates="tool", cascade="all, delete-orphan"
    )


class ToolExecution(Base):
    """One row per real tool invocation — the only source of truth for tool metrics."""
    __tablename__ = "tool_executions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    tool_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tools.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    tenant_id: Mapped[Optional[str]] = mapped_column(String(36), index=True)
    # status: success | failure
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    latency_ms: Mapped[Optional[float]] = mapped_column(Float)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    tool: Mapped["Tool"] = relationship(back_populates="executions")
