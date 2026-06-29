"""
routes/notifications.py

Notifications API — for the frontend notification bell (§1.9).

Endpoints:
  GET  /api/notifications
  POST /api/notifications/{id}/read
"""

from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db.engine import get_db
from db.models.audit import Notification
from security.auth import get_current_user
from services.notification import get_notifications, mark_read
from db.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notifications", tags=["notifications"])

# ── Response schemas ─────────────────────────────────────────────────────

class NotificationOut(BaseModel):
    id: str
    type: str
    message: str
    read_at: str | None
    created_at: str

    @classmethod
    def from_orm(cls, n: Notification) -> "NotificationOut":
        return cls(
            id=n.id,
            type=n.type,
            message=n.message,
            read_at=n.read_at.isoformat() if n.read_at else None,
            created_at=n.created_at.isoformat(),
        )

# ── Routes ───────────────────────────────────────────────────────────────

@router.get("", response_model=List[NotificationOut])
async def list_notifications(
    unread_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[NotificationOut]:
    notifications = await get_notifications(db, current_user.id, unread_only, limit)
    return [NotificationOut.from_orm(n) for n in notifications]

@router.post("/{notification_id}/read", response_model=NotificationOut)
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationOut:
    notif = await mark_read(db, notification_id, current_user.id)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    await db.commit()
    return NotificationOut.from_orm(notif)
