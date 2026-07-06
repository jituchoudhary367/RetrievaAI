"""
services/connector_scheduler.py

Background asyncio task that periodically maintains connector health.

Runs every SCHEDULER_INTERVAL_SECONDS and:
  1. Refreshes expired OAuth tokens (before they expire)
  2. Triggers incremental sync for connectors with auto_sync=True
  3. Retries files stuck in 'syncing' state (stuck jobs)
  4. Cleans up stale webhook channels (renew before expiry)
  5. Updates connector status based on sync state

Started in app/main.py lifespan alongside the health_sampler.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)

SCHEDULER_INTERVAL_SECONDS = 60  # Check every 60 seconds
TOKEN_REFRESH_BUFFER_MINUTES = 10  # Refresh tokens 10 minutes before expiry
WEBHOOK_RENEW_BUFFER_HOURS = 24   # Renew webhooks 24 hours before expiry
STUCK_JOB_TIMEOUT_MINUTES = 60    # Consider a job stuck after 60 minutes


async def run_connector_scheduler() -> None:
    """
    Long-running background task for connector health maintenance.
    Called once from app/main.py lifespan.
    """
    logger.info("Connector scheduler started.")

    while True:
        try:
            await _run_scheduler_cycle()
        except asyncio.CancelledError:
            logger.info("Connector scheduler shutting down.")
            raise
        except Exception as exc:
            logger.error("Connector scheduler error: %s", exc, exc_info=True)

        await asyncio.sleep(SCHEDULER_INTERVAL_SECONDS)


async def _run_scheduler_cycle() -> None:
    """Execute one scheduler cycle."""
    from db.engine import async_session_factory

    async with async_session_factory() as db:
        try:
            await _refresh_expiring_tokens(db)
            await _trigger_auto_incremental_syncs(db)
            await _renew_expiring_webhooks(db)
            await _update_connector_statuses(db)
        except Exception as exc:
            logger.error("Scheduler cycle error: %s", exc, exc_info=True)
            await db.rollback()


async def _refresh_expiring_tokens(db) -> None:
    """Refresh access tokens that expire within TOKEN_REFRESH_BUFFER_MINUTES."""
    from sqlalchemy import select
    from db.models.connector import Connector, ConnectorCredential
    from connectors.google_drive.auth import is_token_expired, refresh_access_token

    buffer = TOKEN_REFRESH_BUFFER_MINUTES * 60  # to seconds

    result = await db.execute(
        select(Connector)
        .where(Connector.status.in_(["connected", "syncing"]))
    )
    connectors = result.scalars().all()

    for connector in connectors:
        cred = connector.credential
        if not cred or not cred.refresh_token:
            continue

        if not is_token_expired(cred.expires_at, buffer_seconds=buffer):
            continue  # Token still fresh

        try:
            # Refresh based on provider
            if connector.provider == "google_drive":
                token_data = await refresh_access_token(cred.refresh_token)
                cred.access_token = token_data["access_token"]
                cred.expires_at = token_data.get("expires_at")
                await db.commit()
                logger.info("Refreshed token for connector %s", connector.id)
        except Exception as exc:
            logger.warning(
                "Failed to refresh token for connector %s: %s",
                connector.id, exc
            )
            connector.status = "error"
            connector.error_message = f"Token refresh failed: {exc}"
            await db.commit()


async def _trigger_auto_incremental_syncs(db) -> None:
    """
    Trigger incremental sync for connectors whose last sync was more than
    sync_interval_minutes ago.
    """
    from sqlalchemy import select
    from db.models.connector import Connector

    result = await db.execute(
        select(Connector)
        .where(
            Connector.status == "connected",
            Connector.auto_sync == True,
        )
    )
    connectors = result.scalars().all()

    now = datetime.now(timezone.utc)

    for connector in connectors:
        sync_state = connector.sync_state
        if not sync_state:
            continue

        # Check if it's time to sync
        last_sync = sync_state.last_sync_completed_at
        interval = timedelta(minutes=connector.sync_interval_minutes)

        if last_sync is None or (now - last_sync) >= interval:
            try:
                from tasks.connector_tasks import sync_connector_incremental_task
                sync_connector_incremental_task.delay(connector.id)
                logger.info(
                    "Auto-triggered incremental sync for connector %s",
                    connector.id
                )
            except Exception as exc:
                logger.warning(
                    "Failed to trigger auto-sync for connector %s: %s",
                    connector.id, exc
                )


async def _renew_expiring_webhooks(db) -> None:
    """Renew webhook channels that expire within WEBHOOK_RENEW_BUFFER_HOURS."""
    from sqlalchemy import select
    from db.models.connector import Connector, ConnectorSyncState
    from app.config import get_settings

    cfg = get_settings()
    if not cfg.connectors.google_drive_webhook_url:
        return  # Webhooks not configured

    buffer = timedelta(hours=WEBHOOK_RENEW_BUFFER_HOURS)
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(Connector).where(Connector.status == "connected")
    )
    connectors = result.scalars().all()

    for connector in connectors:
        sync_state = connector.sync_state
        if not sync_state or not sync_state.webhook_channel_id:
            continue

        if sync_state.webhook_expiry and (sync_state.webhook_expiry - now) > buffer:
            continue  # Webhook still valid

        # Renew webhook
        try:
            from connectors.manager import ConnectorManager
            from connectors.google_drive.auth import is_token_expired

            cred = connector.credential
            if not cred or not cred.access_token:
                continue

            manager = ConnectorManager(connector.provider)
            import uuid
            new_channel_id = str(uuid.uuid4())

            watch = await manager.setup_watch(
                cred.access_token,
                cfg.connectors.google_drive_webhook_url,
                new_channel_id,
            )

            if watch:
                # Stop old channel
                if sync_state.webhook_resource_id:
                    await manager.stop_watch(
                        cred.access_token,
                        sync_state.webhook_channel_id,
                        sync_state.webhook_resource_id,
                    )

                sync_state.webhook_channel_id = watch.channel_id
                sync_state.webhook_resource_id = watch.resource_id
                sync_state.webhook_expiry = watch.expiry
                await db.commit()
                logger.info("Renewed webhook for connector %s", connector.id)

        except Exception as exc:
            logger.warning(
                "Failed to renew webhook for connector %s: %s",
                connector.id, exc
            )


async def _update_connector_statuses(db) -> None:
    """Update connector status based on latest sync state."""
    from sqlalchemy import select
    from db.models.connector import Connector, ConnectorFile

    result = await db.execute(
        select(Connector).where(Connector.status == "syncing")
    )
    connectors = result.scalars().all()

    now = datetime.now(timezone.utc)
    stuck_threshold = now - timedelta(minutes=STUCK_JOB_TIMEOUT_MINUTES)

    for connector in connectors:
        sync_state = connector.sync_state
        if not sync_state:
            continue

        # If still syncing but no pending files remain, mark as connected
        started_at = sync_state.last_sync_started_at
        if started_at and started_at < stuck_threshold:
            # Sync has been running too long — check if files are done
            from sqlalchemy import func
            pending_count = (await db.execute(
                select(func.count()).select_from(ConnectorFile)
                .where(
                    ConnectorFile.connector_id == connector.id,
                    ConnectorFile.sync_status.in_(["pending", "syncing"]),
                )
            )).scalar_one()

            if pending_count == 0:
                connector.status = "connected"
                if sync_state:
                    sync_state.last_sync_status = "success"
                    sync_state.last_sync_completed_at = now
                await db.commit()
                logger.info("Connector %s sync completed.", connector.id)


__all__ = ["run_connector_scheduler"]
