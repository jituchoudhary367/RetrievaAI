"""
services/audit.py

AuditLogEntry writer (§1.9).

Every admin-level mutation calls `log_action()` — it's fire-and-forget
so it never blocks the HTTP response.

Usage:
    from services.audit import log_action
    await log_action(
        actor_user_id=user.id,
        action="document.delete",
        target=f"document:{doc_id}",
        detail={"title": doc.title},
    )
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from db.engine import async_session_factory
from db.models.audit import AuditLogEntry

logger = logging.getLogger(__name__)


async def log_action(
    *,
    actor_user_id: Optional[str],
    action: str,
    target: Optional[str] = None,
    detail: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Write an AuditLogEntry row.

    Fire-and-forget — call with `asyncio.create_task(log_action(...))` to
    avoid blocking the response, or await it if you need the write confirmed.
    """
    try:
        async with async_session_factory() as db:
            db.add(AuditLogEntry(
                actor_user_id=actor_user_id,
                action=action,
                target=target,
                detail=json.dumps(detail) if detail else None,
            ))
            await db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("AuditLog: failed to write %s action: %s", action, exc)


__all__ = ["log_action"]
