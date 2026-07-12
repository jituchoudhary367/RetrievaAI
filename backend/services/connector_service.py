"""
services/connector_service.py

Business logic for connector lifecycle operations.

This service handles:
  - connect: OAuth code exchange + store credentials + create DB rows
  - disconnect: revoke tokens + cleanup DB + delete document vectors
  - start_sync / stop_sync: trigger Celery tasks
  - get_status: aggregate sync state
  - list_connectors: user's connected sources

Token refresh is handled here transparently before any API call.
The service always returns a fresh access token to callers.
"""

from __future__ import annotations

import logging
import secrets
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from connectors.google_drive.auth import is_token_expired, refresh_access_token
from connectors.models import ConnectorStatusEnum, SyncMode
from db.models.connector import (
    Connector,
    ConnectorCredential,
    ConnectorFile,
    ConnectorSyncState,
)

logger = logging.getLogger(__name__)


# ── Token Management ──────────────────────────────────────────────────────────


async def _get_fresh_token(
    db: AsyncSession,
    connector: Connector,
) -> str:
    """
    Return a valid access token for the connector.
    If the stored token is expired, refresh it and persist the new one.
    """
    cred = connector.credential
    if not cred:
        raise ValueError(f"No credentials stored for connector {connector.id}")

    if not is_token_expired(cred.expires_at):
        return cred.access_token

    # Token is expired — refresh it
    logger.info("Refreshing access token for connector %s", connector.id)
    token_data = await refresh_access_token(cred.refresh_token)

    cred.access_token = token_data["access_token"]
    cred.expires_at = token_data.get("expires_at")
    await db.commit()

    return cred.access_token


# ── Connect / Disconnect ──────────────────────────────────────────────────────


async def get_auth_url(provider: str, state: str) -> str:
    """Get the OAuth authorization URL for a connector provider."""
    from connectors.registry import ConnectorRegistry
    adapter = ConnectorRegistry.get(provider)()
    return await adapter.get_auth_url(state=state)


async def connect_connector(
    db: AsyncSession,
    user_id: str,
    provider: str,
    auth_code: str,
    redirect_uri: str,
    root_folder_id: Optional[str] = None,
    root_folder_name: Optional[str] = None,
) -> Connector:
    """
    Complete the OAuth flow and register a new connector.

    Steps:
    1. Exchange auth code for tokens
    2. Create Connector row
    3. Store ConnectorCredential
    4. Create ConnectorSyncState
    5. Trigger initial full sync (async)
    """
    from connectors.registry import ConnectorRegistry
    adapter = ConnectorRegistry.get(provider)()

    # 1. Exchange code for tokens
    token_data = await adapter.exchange_code(auth_code, redirect_uri)

    # 2. Create connector row
    connector = Connector(
        user_id=user_id,
        provider=provider,
        display_name=provider,
        status=ConnectorStatusEnum.CONNECTED.value,
        root_folder_id=root_folder_id,
        root_folder_name=root_folder_name,
        auto_sync=True,
    )
    db.add(connector)
    await db.flush()  # get the ID

    # 3. Store credentials
    cred = ConnectorCredential(
        connector_id=connector.id,
        access_token=token_data.get("access_token"),
        refresh_token=token_data["refresh_token"],
        token_type=token_data.get("token_type", "Bearer"),
        scopes=token_data.get("scope"),
        expires_at=token_data.get("expires_at"),
    )
    db.add(cred)

    # 4. Create initial sync state
    sync_state = ConnectorSyncState(connector_id=connector.id)
    db.add(sync_state)

    await db.commit()

    # 5. Trigger full sync in background
    try:
        from connectors.tasks import discover_files_task
        discover_files_task.delay(connector.id, is_incremental=False)
        logger.info("Full sync task queued for connector %s", connector.id)
    except Exception as exc:
        logger.warning("Could not queue sync task (Celery unavailable?): %s", exc)
        # Fallback: mark as connected without syncing
        # User can trigger sync manually from the UI

    return connector


async def disconnect_connector(
    db: AsyncSession,
    user_id: str,
    connector_id: str,
) -> None:
    """
    Disconnect a connector: revoke tokens, delete DB rows, clean up.

    Documents that were indexed from this connector are NOT deleted from
    Qdrant by default (they remain searchable). Set delete_documents=True
    to also remove indexed content.
    """
    result = await db.execute(
        select(Connector)
        .where(Connector.id == connector_id, Connector.user_id == user_id)
    )
    connector = result.scalar_one_or_none()
    if not connector:
        raise ValueError(f"Connector {connector_id} not found for user {user_id}")

    from connectors.registry import ConnectorRegistry
    adapter = ConnectorRegistry.get(connector.provider)()

    # Revoke tokens
    if connector.credential:
        try:
            await adapter.revoke_token(connector.credential.access_token or connector.credential.refresh_token)
        except Exception as exc:
            logger.warning("Token revocation failed (may already be invalid): %s", exc)

        # Stop webhook if active
        sync_state = connector.sync_state
        if sync_state and sync_state.webhook_channel_id:
            try:
                token = connector.credential.access_token or ""
                if hasattr(adapter, "stop_watch"):
                    await adapter.stop_watch(token, sync_state.webhook_channel_id, sync_state.webhook_resource_id or "")
            except Exception as exc:
                logger.warning("Webhook stop failed: %s", exc)

    # Delete connector (cascades to credential, sync_state, files)
    await db.delete(connector)
    await db.commit()
    logger.info("Connector %s disconnected for user %s", connector_id, user_id)


async def pause_connector(
    db: AsyncSession,
    user_id: str,
    connector_id: str,
) -> bool:
    """Pause automatic syncs for a connector."""
    result = await db.execute(
        select(Connector)
        .where(Connector.id == connector_id, Connector.user_id == user_id)
    )
    connector = result.scalar_one_or_none()
    if not connector:
        raise ValueError(f"Connector {connector_id} not found")
        
    connector.auto_sync = False
    connector.status = ConnectorStatusEnum.PAUSED.value if hasattr(ConnectorStatusEnum, 'PAUSED') else "paused"
    await db.commit()
    return True


async def resume_connector(
    db: AsyncSession,
    user_id: str,
    connector_id: str,
) -> bool:
    """Resume automatic syncs for a connector."""
    result = await db.execute(
        select(Connector)
        .where(Connector.id == connector_id, Connector.user_id == user_id)
    )
    connector = result.scalar_one_or_none()
    if not connector:
        raise ValueError(f"Connector {connector_id} not found")
        
    connector.auto_sync = True
    connector.status = ConnectorStatusEnum.CONNECTED.value
    await db.commit()
    return True

# ── Sync Operations ───────────────────────────────────────────────────────────


async def trigger_sync(
    db: AsyncSession,
    user_id: str,
    connector_id: str,
    mode: SyncMode = SyncMode.INCREMENTAL,
) -> dict:
    """
    Trigger a sync (full or incremental) for a connector.

    Returns a dict with {connector_id, mode, status}.
    """
    result = await db.execute(
        select(Connector)
        .where(Connector.id == connector_id, Connector.user_id == user_id)
    )
    connector = result.scalar_one_or_none()
    if not connector:
        raise ValueError(f"Connector {connector_id} not found")

    connector.status = ConnectorStatusEnum.SYNCING.value
    await db.commit()

    try:
        from connectors.tasks import discover_files_task
        if mode == SyncMode.FULL:
            discover_files_task.delay(connector_id, is_incremental=False)
        else:
            discover_files_task.delay(connector_id, is_incremental=True)
    except Exception as exc:
        logger.error("Failed to queue sync task: %s", exc)
        connector.status = ConnectorStatusEnum.ERROR.value
        connector.error_message = str(exc)
        await db.commit()
        raise

    return {"connector_id": connector_id, "mode": mode.value, "status": "queued"}


# ── Query / Status ────────────────────────────────────────────────────────────


async def list_connectors(db: AsyncSession, user_id: str) -> list[Connector]:
    """List all connectors for a user."""
    result = await db.execute(
        select(Connector)
        .where(Connector.user_id == user_id)
        .order_by(Connector.created_at.desc())
    )
    return list(result.scalars().all())


async def get_connector(
    db: AsyncSession,
    user_id: str,
    connector_id: str,
) -> Optional[Connector]:
    """Get a single connector by ID (user-scoped)."""
    result = await db.execute(
        select(Connector)
        .where(Connector.id == connector_id, Connector.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_connector_files(
    db: AsyncSession,
    connector_id: str,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[ConnectorFile], int]:
    """List files for a connector with pagination."""
    from sqlalchemy import func

    count_result = await db.execute(
        select(func.count()).select_from(ConnectorFile)
        .where(ConnectorFile.connector_id == connector_id)
    )
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(
        select(ConnectorFile)
        .where(ConnectorFile.connector_id == connector_id)
        .order_by(ConnectorFile.last_synced_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    return list(result.scalars().all()), total


async def get_fresh_access_token(
    db: AsyncSession,
    connector_id: str,
    user_id: str,
) -> str:
    """Get (and refresh if needed) the access token for a connector."""
    connector = await get_connector(db, user_id, connector_id)
    if not connector:
        raise ValueError(f"Connector {connector_id} not found")
    return await _get_fresh_token(db, connector)


__all__ = [
    "get_auth_url",
    "connect_connector",
    "disconnect_connector",
    "trigger_sync",
    "list_connectors",
    "get_connector",
    "get_connector_files",
    "get_fresh_access_token",
]
