"""
db/models/security.py

ApiKey ORM model (§1.8).

ApiKey — powers Security Settings > API Key panel.
         Stores only the hashed key; the raw key is shown to the user
         exactly once on creation and never stored.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, _new_uuid


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    # prefix: first 8 chars of the raw key shown in the UI list (e.g. "sk-abc123")
    prefix: Mapped[Optional[str]] = mapped_column(String(16))
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User", back_populates="api_keys"
    )
