"""
db/models/user.py

User and UserSession ORM models.

UserSession enables per-device session revocation (§1.8) via a `jti` claim
on the JWT, independently of the coarser `token_version` mechanism on User.
User.totp_secret enables minimal TOTP 2FA (§1.8).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, TimestampMixin, TenantMixin, _new_uuid


class User(Base, TimestampMixin, TenantMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(255))
    roles: Mapped[str] = mapped_column(
        Text, default="VIEWER",
        comment="Comma-separated role list, e.g. VIEWER,TENANT_ADMIN"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    token_version: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False,
        comment="Increment to invalidate all sessions at once (e.g. after password reset)"
    )
    totp_secret: Mapped[Optional[str]] = mapped_column(
        String(64), comment="Base32 TOTP secret; null means 2FA not enabled"
    )
    # Email verification / password-reset
    verification_token: Mapped[Optional[str]] = mapped_column(String(255))
    verification_token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    reset_token: Mapped[Optional[str]] = mapped_column(String(255))
    reset_token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    sessions: Mapped[list["UserSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    api_keys: Mapped[list["ApiKey"]] = relationship(  # type: ignore[name-defined]
        "ApiKey", back_populates="user", cascade="all, delete-orphan"
    )


class UserSession(Base, TenantMixin):
    """One row per active login session — identified by `session_jti` on the JWT."""
    __tablename__ = "user_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_jti: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="sessions")
