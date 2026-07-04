"""
db/models/auth_token.py

AuthToken ORM model for email verification and password resets.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base, TimestampMixin, _new_uuid

class AuthToken(Base, TimestampMixin):
    __tablename__ = "auth_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    purpose: Mapped[str] = mapped_column(String(32), nullable=False) # "email_verify" or "password_reset"
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
