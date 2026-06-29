"""
services/notification.py

Notification creation and retrieval (§1.9).

Polled, not pushed — GET /api/notifications returns unread notifications.
Notifications are written when:
  - An ingestion job completes or fails
  - An invite is accepted (future)
  - An eval run finishes
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.engine import async_session_factory
from db.models.audit import Notification

logger = logging.getLogger(__name__)

NotificationType = str  # "ingestion_complete" | "ingestion_failed" | "eval_complete" | ...


async def create_notification(
    *,
    user_id: str,
    type: NotificationType,
    message: str,
) -> None:
    """Create a Notification row for a user."""
    try:
        async with async_session_factory() as db:
            db.add(Notification(user_id=user_id, type=type, message=message))
            await db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Notification: failed to create for user %s: %s", user_id, exc)


async def get_notifications(
    db: AsyncSession,
    user_id: str,
    unread_only: bool = False,
    limit: int = 50,
) -> List[Notification]:
    """Return notifications for *user_id*, newest first."""
    q = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        q = q.where(Notification.read_at.is_(None))
    q = q.order_by(Notification.created_at.desc()).limit(limit)
    result = await db.execute(q)
    return list(result.scalars().all())


async def mark_read(
    db: AsyncSession,
    notification_id: str,
    user_id: str,
) -> Optional[Notification]:
    """Mark a notification as read. Returns the updated row or None if not found."""
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
    )
    notif = result.scalar_one_or_none()
    if notif is None:
        return None
    notif.read_at = datetime.now(timezone.utc)
    return notif


__all__ = ["create_notification", "get_notifications", "mark_read"]
