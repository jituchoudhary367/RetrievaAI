"""
routes/connectors.py

REST API endpoints for the connector framework.

Endpoints:
  GET    /api/connectors                         — list user's connectors
  GET    /api/connectors/providers               — list available providers
  GET    /api/connectors/google-drive/auth       — get OAuth URL
  GET    /api/connectors/google-drive/callback   — OAuth callback
  DELETE /api/connectors/{id}                    — disconnect connector
  POST   /api/connectors/{id}/sync               — trigger sync
  GET    /api/connectors/{id}/status             — sync status
  GET    /api/connectors/{id}/files              — list synced files
  POST   /api/connectors/webhook                 — Google Drive webhook receiver
"""

from __future__ import annotations

import hashlib
import logging
import secrets
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from connectors.models import SyncMode
from connectors.registry import ConnectorRegistry
from db.engine import get_db
from db.models.connector import Connector, ConnectorFile, ConnectorSyncState
from db.models.user import User
from security.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/connectors", tags=["connectors"])


# ── Response Models ───────────────────────────────────────────────────────────

class ConnectorOut(BaseModel):
    id: str
    provider: str
    display_name: Optional[str]
    status: str
    auto_sync: bool
    sync_interval_minutes: int
    root_folder_name: Optional[str]
    error_message: Optional[str]
    created_at: str
    last_sync_at: Optional[str]
    files_synced: int
    files_failed: int

    @classmethod
    def from_orm(cls, c: Connector) -> "ConnectorOut":
        last_sync = None
        files_synced = 0
        files_failed = 0

        if c.sync_state:
            if c.sync_state.last_sync_completed_at:
                last_sync = c.sync_state.last_sync_completed_at.isoformat()
            files_synced = c.sync_state.files_synced or 0
            files_failed = c.sync_state.files_failed or 0

        return cls(
            id=c.id,
            provider=c.provider,
            display_name=c.display_name,
            status=c.status,
            auto_sync=c.auto_sync,
            sync_interval_minutes=c.sync_interval_minutes,
            root_folder_name=c.root_folder_name,
            error_message=c.error_message,
            created_at=c.created_at.isoformat(),
            last_sync_at=last_sync,
            files_synced=files_synced,
            files_failed=files_failed,
        )


class ConnectorFileOut(BaseModel):
    id: str
    remote_file_id: str
    remote_file_name: Optional[str]
    remote_mime_type: Optional[str]
    sync_status: str
    sync_error: Optional[str]
    document_id: Optional[str]
    last_synced_at: Optional[str]
    remote_url: Optional[str]

    @classmethod
    def from_orm(cls, f: ConnectorFile) -> "ConnectorFileOut":
        return cls(
            id=f.id,
            remote_file_id=f.remote_file_id,
            remote_file_name=f.remote_file_name,
            remote_mime_type=f.remote_mime_type,
            sync_status=f.sync_status,
            sync_error=f.sync_error,
            document_id=f.document_id,
            last_synced_at=f.last_synced_at.isoformat() if f.last_synced_at else None,
            remote_url=f.remote_url,
        )


class SyncRequest(BaseModel):
    mode: str = "incremental"  # "full" | "incremental"


class SyncStatusOut(BaseModel):
    connector_id: str
    status: str
    last_sync_mode: Optional[str]
    last_sync_started_at: Optional[str]
    last_sync_completed_at: Optional[str]
    last_sync_status: Optional[str]
    files_discovered: int
    files_synced: int
    files_failed: int
    change_token_set: bool


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/providers")
async def list_providers() -> List[Dict[str, str]]:
    """List all available connector providers."""
    providers = ConnectorRegistry.list_providers()
    return [{"provider": p} for p in providers]


@router.get("", response_model=List[ConnectorOut])
async def list_connectors(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ConnectorOut]:
    """List all connectors for the current user."""
    from services.connector_service import list_connectors as svc_list

    connectors = await svc_list(db, current_user.id)
    return [ConnectorOut.from_orm(c) for c in connectors]


@router.get("/google-drive/auth")
async def google_drive_auth(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    """
    Get the Google Drive OAuth2 authorization URL.
    The frontend should redirect the user to this URL.
    """
    from services.connector_service import get_auth_url

    # Generate CSRF state token (in production, store in session or Redis)
    state = f"{current_user.id}:{secrets.token_urlsafe(16)}"

    auth_url = await get_auth_url("google_drive", state=state)
    return {"auth_url": auth_url, "state": state}


@router.get("/google-drive/callback")
async def google_drive_callback(
    code: str = Query(...),
    state: str = Query(...),
    error: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """
    Google Drive OAuth2 callback endpoint.

    Google redirects here after user grants permission.
    Exchanges code for tokens, creates connector, redirects to frontend.
    """
    cfg = get_settings()

    if error:
        frontend_url = f"{cfg.frontend_base_url}/settings?connector_error={error}"
        return RedirectResponse(url=frontend_url)

    # Extract user_id from state (format: "user_id:random_token")
    try:
        user_id = state.split(":")[0]
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    try:
        from services.connector_service import connect_connector

        connector = await connect_connector(
            db=db,
            user_id=user_id,
            provider="google_drive",
            auth_code=code,
            redirect_uri=cfg.connectors.google_drive_redirect_uri,
        )

        frontend_url = (
            f"{cfg.frontend_base_url}/settings"
            f"?connector_id={connector.id}"
            f"&connector_status=connected"
        )
        return RedirectResponse(url=frontend_url)

    except Exception as exc:
        logger.error("Google Drive callback failed: %s", exc, exc_info=True)
        import urllib.parse
        error_msg = urllib.parse.quote(str(exc))
        frontend_url = f"{cfg.frontend_base_url}/settings?connector_error={error_msg}"
        return RedirectResponse(url=frontend_url)


@router.delete("/{connector_id}", status_code=204, response_model=None)
async def disconnect_connector(
    connector_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Disconnect a connector and clean up credentials."""
    from fastapi import Response as FastResponse
    from services.connector_service import disconnect_connector as svc_disconnect

    try:
        await svc_disconnect(db, current_user.id, connector_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return FastResponse(status_code=204)



@router.post("/{connector_id}/pause")
async def pause_connector(
    connector_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    """Pause automatic syncs for a connector."""
    from services.connector_service import pause_connector as svc_pause
    try:
        await svc_pause(db, current_user.id, connector_id)
        return {"status": "paused"}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/{connector_id}/resume")
async def resume_connector(
    connector_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    """Resume automatic syncs for a connector."""
    from services.connector_service import resume_connector as svc_resume
    try:
        await svc_resume(db, current_user.id, connector_id)
        return {"status": "resumed"}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/{connector_id}/sync")
async def trigger_sync(
    connector_id: str,
    body: SyncRequest = SyncRequest(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Trigger a sync (full or incremental) for a connector."""
    from services.connector_service import trigger_sync as svc_sync

    mode = SyncMode.FULL if body.mode == "full" else SyncMode.INCREMENTAL

    try:
        result = await svc_sync(db, current_user.id, connector_id, mode)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("Sync trigger failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{connector_id}/status", response_model=SyncStatusOut)
async def get_sync_status(
    connector_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SyncStatusOut:
    """Get current sync status for a connector."""
    result = await db.execute(
        select(Connector)
        .where(Connector.id == connector_id, Connector.user_id == current_user.id)
    )
    connector = result.scalar_one_or_none()
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")

    sync_state = connector.sync_state

    return SyncStatusOut(
        connector_id=connector.id,
        status=connector.status,
        last_sync_mode=sync_state.last_sync_mode if sync_state else None,
        last_sync_started_at=(
            sync_state.last_sync_started_at.isoformat()
            if sync_state and sync_state.last_sync_started_at else None
        ),
        last_sync_completed_at=(
            sync_state.last_sync_completed_at.isoformat()
            if sync_state and sync_state.last_sync_completed_at else None
        ),
        last_sync_status=sync_state.last_sync_status if sync_state else None,
        files_discovered=sync_state.files_discovered if sync_state else 0,
        files_synced=sync_state.files_synced if sync_state else 0,
        files_failed=sync_state.files_failed if sync_state else 0,
        change_token_set=bool(sync_state and sync_state.change_token) if sync_state else False,
    )


@router.get("/{connector_id}/files", response_model=List[ConnectorFileOut])
async def list_connector_files(
    connector_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    status_filter: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ConnectorFileOut]:
    """
    List files tracked by a connector.
    Optionally filter by sync_status (indexed, failed, pending, deleted).
    """
    # Verify ownership
    result = await db.execute(
        select(Connector)
        .where(Connector.id == connector_id, Connector.user_id == current_user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Connector not found")

    query = select(ConnectorFile).where(
        ConnectorFile.connector_id == connector_id
    )
    if status_filter:
        query = query.where(ConnectorFile.sync_status == status_filter)

    offset = (page - 1) * page_size
    query = query.order_by(ConnectorFile.last_synced_at.desc()).offset(offset).limit(page_size)

    files_result = await db.execute(query)
    files = files_result.scalars().all()
    return [ConnectorFileOut.from_orm(f) for f in files]


@router.post("/webhook")
async def google_drive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    """
    Receive Google Drive push notification webhooks.

    Google sends a POST request with headers identifying the channel.
    We validate, then trigger an incremental sync for the affected connector.
    """
    channel_id = request.headers.get("X-Goog-Channel-ID")
    resource_id = request.headers.get("X-Goog-Resource-ID")
    resource_state = request.headers.get("X-Goog-Resource-State")

    if not channel_id:
        raise HTTPException(status_code=400, detail="Missing X-Goog-Channel-ID")

    logger.info(
        "Webhook received: channel=%s resource_state=%s",
        channel_id, resource_state
    )

    # 'sync' state is the initial verification ping — acknowledge it
    if resource_state == "sync":
        return {"status": "acknowledged"}

    # Find the connector for this channel
    result = await db.execute(
        select(ConnectorSyncState)
        .where(ConnectorSyncState.webhook_channel_id == channel_id)
    )
    sync_state = result.scalar_one_or_none()

    if not sync_state:
        logger.warning("Webhook for unknown channel %s", channel_id)
        return {"status": "ignored"}

    # Trigger incremental sync in background
    background_tasks.add_task(
        _trigger_webhook_sync,
        connector_id=sync_state.connector_id,
    )

    return {"status": "queued"}


def _trigger_webhook_sync(connector_id: str) -> None:
    """Trigger incremental sync from webhook (background task)."""
    try:
        from tasks.connector_tasks import sync_connector_incremental_task
        sync_connector_incremental_task.delay(connector_id)
        logger.info("Webhook sync queued for connector %s", connector_id)
    except Exception as exc:
        logger.error("Failed to queue webhook sync: %s", exc)


__all__ = ["router"]
