"""
tasks/connector_tasks.py

Celery tasks for connector sync operations.

Phases 7–11:
  - sync_connector_file_task      (Phase 7/8): Download + ingest a single file
  - sync_connector_full_task      (Phase 8): List all files, queue one task per file
  - sync_connector_incremental_task (Phase 9): Get changes, queue modified files
  - delete_connector_file_task    (Phase 10): Delete vectors + document row
  - handle_file_update_task       (Phase 11): Re-index a changed file

Design:
  - Each task processes ONE file at a time. Never queue an entire Drive.
  - Failed tasks are retried up to MAX_RETRIES times with exponential backoff.
  - Only failed files are retried, never the full sync.
  - All tasks are scoped by connector_id — never cross user boundaries.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from celery import shared_task
from celery.utils.log import get_task_logger

from tasks.celery_app import celery_app

logger = get_task_logger(__name__)

MAX_RETRIES = 3
RETRY_DELAY = 60  # seconds (exponential: 60, 120, 240)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_sync_db():
    """Synchronous DB session for Celery worker processes."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.config import get_settings

    cfg = get_settings()
    engine = create_engine(
        cfg.database.sync_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    return engine, factory()


def _get_fresh_token_sync(db, connector) -> str:
    """Get (and refresh if needed) the access token synchronously."""
    from connectors.google_drive.auth import is_token_expired, refresh_access_token
    import asyncio

    cred = connector.credential
    if not cred:
        raise ValueError(f"No credentials for connector {connector.id}")

    if not is_token_expired(cred.expires_at):
        return cred.access_token

    # Refresh
    async def _refresh():
        return await refresh_access_token(cred.refresh_token)

    token_data = asyncio.run(_refresh())
    cred.access_token = token_data["access_token"]
    cred.expires_at = token_data.get("expires_at")
    db.commit()
    return cred.access_token


# ── Phase 8: Single File Task ─────────────────────────────────────────────────

@celery_app.task(
    bind=True,
    name="connector_tasks.sync_connector_file_task",
    max_retries=MAX_RETRIES,
    default_retry_delay=RETRY_DELAY,
    acks_late=True,
)
def sync_connector_file_task(self, connector_id: str, remote_file_id: str) -> Optional[str]:
    """
    Download and ingest a single file from a connector.

    This is the atomic unit of work. One task = one file.
    On failure, retries with exponential backoff up to MAX_RETRIES.
    """
    engine, db = _get_sync_db()
    try:
        from sqlalchemy import select
        from db.models.connector import Connector

        connector = db.get(Connector, connector_id)
        if not connector:
            logger.error("Connector %s not found — skipping file %s", connector_id, remote_file_id)
            return None

        access_token = _get_fresh_token_sync(db, connector)
        db.close()
        engine.dispose()

        from services.ingestion_orchestrator import orchestrate_file_ingestion
        document_id = orchestrate_file_ingestion(connector_id, remote_file_id, access_token)

        if document_id:
            logger.info("File %s → document %s (connector %s)", remote_file_id, document_id, connector_id)
        else:
            logger.warning("File %s ingestion failed for connector %s", remote_file_id, connector_id)

        return document_id

    except Exception as exc:
        logger.error("sync_connector_file_task failed: %s", exc, exc_info=True)
        try:
            db.close()
            engine.dispose()
        except Exception:
            pass
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=RETRY_DELAY * (2 ** self.request.retries))


# ── Phase 8: Full Sync ────────────────────────────────────────────────────────

@celery_app.task(
    bind=True,
    name="connector_tasks.sync_connector_full_task",
    max_retries=1,
    acks_late=True,
)
def sync_connector_full_task(self, connector_id: str) -> dict:
    """
    Full sync: list ALL files in the connected source, queue one task per file.

    Never downloads files directly — only enqueues sync_connector_file_task
    for each discovered file.
    """
    import asyncio
    from sqlalchemy import select
    from db.models.connector import Connector, ConnectorFile, ConnectorSyncState
    from connectors.manager import ConnectorManager

    engine, db = _get_sync_db()
    files_queued = 0
    files_discovered = 0

    try:
        connector = db.get(Connector, connector_id)
        if not connector:
            logger.error("Connector %s not found for full sync", connector_id)
            return {"status": "error", "reason": "connector_not_found"}

        # Update sync state
        if connector.sync_state:
            connector.sync_state.last_sync_started_at = datetime.now(timezone.utc)
            connector.sync_state.last_sync_mode = "full"
            connector.sync_state.last_sync_status = "running"
        connector.status = "syncing"
        db.commit()

        access_token = _get_fresh_token_sync(db, connector)
        root_folder_id = connector.root_folder_id
        manager = ConnectorManager(connector.provider)
        db.close()
        engine.dispose()

        # Paginate through all files
        page_token = None
        all_file_ids = []

        while True:
            async def _list_page():
                return await manager.list_files(access_token, folder_id=root_folder_id, page_token=page_token)

            result = asyncio.run(_list_page())
            all_file_ids.extend([(f.file_id, f.name, f.mime_type, f.modified_at) for f in result.files])
            files_discovered += len(result.files)

            if not result.has_more:
                break
            page_token = result.next_page_token
            
        import os
        use_framework = os.environ.get("USE_CONNECTOR_FRAMEWORK", "false").lower() == "true"
        if use_framework and connector.provider == "google_drive":
            try:
                from connectors.google_drive.adapter import GoogleDriveConnector
                adapter = GoogleDriveConnector()
                async def _shadow_sync():
                    await adapter.authenticate({"access_token": access_token})
                    new_files = []
                    async for f in adapter.full_sync():
                        new_files.append(f.external_id)
                    return new_files
                shadow_ids = asyncio.run(_shadow_sync())
                old_ids = [fid for fid, _, _, _ in all_file_ids]
                diff = set(old_ids) ^ set(shadow_ids)
                if diff:
                    logger.error("SHADOW MODE MISMATCH in full_sync! Diff: %s", diff)
                else:
                    logger.info("SHADOW MODE SUCCESS: full_sync returned identical files.")
            except Exception as shadow_exc:
                logger.error("SHADOW MODE FAILED: %s", shadow_exc, exc_info=True)

        logger.info("Full sync for %s: discovered %d files", connector_id, files_discovered)

        # Re-open DB to create ConnectorFile rows
        engine2, db2 = _get_sync_db()
        try:
            for file_id, file_name, mime_type, modified_at in all_file_ids:
                # Check if file already tracked
                existing = db2.execute(
                    select(ConnectorFile).where(
                        ConnectorFile.connector_id == connector_id,
                        ConnectorFile.remote_file_id == file_id,
                    )
                ).scalar_one_or_none()

                if existing and existing.sync_status == "indexed":
                    # Already indexed — check if modified
                    if modified_at and existing.remote_modified_at:
                        if modified_at <= existing.remote_modified_at:
                            continue  # No change, skip

                if not existing:
                    connector_file = ConnectorFile(
                        connector_id=connector_id,
                        remote_file_id=file_id,
                        remote_file_name=file_name,
                        remote_mime_type=mime_type,
                        remote_modified_at=modified_at,
                        sync_status="pending",
                    )
                    db2.add(connector_file)
                else:
                    existing.sync_status = "pending"
                    existing.remote_modified_at = modified_at

                # Queue individual file task
                sync_connector_file_task.delay(connector_id, file_id)
                files_queued += 1

            db2.commit()

            # Update sync state
            conn2 = db2.get(Connector, connector_id)
            if conn2 and conn2.sync_state:
                conn2.sync_state.files_discovered = files_discovered

                # Get and store change token for future incremental syncs
                try:
                    async def _get_token():
                        return await manager.get_initial_change_token(access_token)

                    change_token = asyncio.run(_get_token())
                    conn2.sync_state.change_token = change_token
                except Exception as exc:
                    logger.warning("Could not get change token: %s", exc)

            db2.commit()
        finally:
            db2.close()
            engine2.dispose()

        logger.info(
            "Full sync queued %d/%d files for connector %s",
            files_queued, files_discovered, connector_id
        )
        return {"status": "queued", "files_discovered": files_discovered, "files_queued": files_queued}

    except Exception as exc:
        logger.error("Full sync failed for connector %s: %s", connector_id, exc, exc_info=True)
        try:
            engine3, db3 = _get_sync_db()
            conn3 = db3.get(Connector, connector_id)
            if conn3:
                conn3.status = "error"
                conn3.error_message = str(exc)
                if conn3.sync_state:
                    conn3.sync_state.last_sync_status = "failed"
                    conn3.sync_state.last_sync_error = str(exc)
                    conn3.sync_state.last_sync_completed_at = datetime.now(timezone.utc)
                db3.commit()
            db3.close()
            engine3.dispose()
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=300)


# ── Phase 9: Incremental Sync ─────────────────────────────────────────────────

@celery_app.task(
    bind=True,
    name="connector_tasks.sync_connector_incremental_task",
    max_retries=3,
    acks_late=True,
)
def sync_connector_incremental_task(self, connector_id: str) -> dict:
    """
    Incremental sync: get only changed/new/deleted files since last sync.
    Uses Google Drive Changes API with stored change_token.
    """
    import asyncio
    from sqlalchemy import select
    from db.models.connector import Connector, ConnectorFile, ConnectorSyncState
    from connectors.manager import ConnectorManager
    from connectors.models import FileChangeType

    engine, db = _get_sync_db()
    files_queued = 0
    files_deleted = 0

    try:
        connector = db.get(Connector, connector_id)
        if not connector:
            logger.error("Connector %s not found for incremental sync", connector_id)
            return {"status": "error", "reason": "connector_not_found"}

        if not connector.sync_state or not connector.sync_state.change_token:
            logger.info("No change token for %s — triggering full sync instead", connector_id)
            db.close()
            engine.dispose()
            sync_connector_full_task.delay(connector_id)
            return {"status": "queued_full_sync", "reason": "no_change_token"}

        change_token = connector.sync_state.change_token
        access_token = _get_fresh_token_sync(db, connector)

        connector.status = "syncing"
        if connector.sync_state:
            connector.sync_state.last_sync_started_at = datetime.now(timezone.utc)
            connector.sync_state.last_sync_mode = "incremental"
            connector.sync_state.last_sync_status = "running"
        db.commit()
        db.close()
        engine.dispose()

        manager = ConnectorManager(connector.provider)

        # Get all changes since last token
        all_changes = []
        current_token = change_token

        while True:
            async def _get_changes():
                return await manager.get_changes(access_token, current_token)

            change_list = asyncio.run(_get_changes())
            all_changes.extend(change_list.changes)
            current_token = change_list.new_change_token

            if not change_list.has_more:
                break

        logger.info(
            "Incremental sync for %s: %d changes since last token",
            connector_id, len(all_changes)
        )

        # Process changes
        engine2, db2 = _get_sync_db()
        try:
            for change in all_changes:
                if change.change_type == FileChangeType.DELETED:
                    # Handle deletion (Phase 10)
                    delete_connector_file_task.delay(connector_id, change.file_id)
                    files_deleted += 1
                else:
                    # Handle add/modify (Phase 11)
                    existing = db2.execute(
                        select(ConnectorFile).where(
                            ConnectorFile.connector_id == connector_id,
                            ConnectorFile.remote_file_id == change.file_id,
                        )
                    ).scalar_one_or_none()

                    if not existing:
                        cf = ConnectorFile(
                            connector_id=connector_id,
                            remote_file_id=change.file_id,
                            remote_file_name=change.file_metadata.name if change.file_metadata else None,
                            remote_mime_type=change.file_metadata.mime_type if change.file_metadata else None,
                            remote_modified_at=change.file_metadata.modified_at if change.file_metadata else None,
                            sync_status="pending",
                        )
                        db2.add(cf)
                    else:
                        existing.sync_status = "pending"
                        if change.file_metadata:
                            existing.remote_modified_at = change.file_metadata.modified_at

                    sync_connector_file_task.delay(connector_id, change.file_id)
                    files_queued += 1

            # Update change token
            conn2 = db2.get(Connector, connector_id)
            if conn2 and conn2.sync_state:
                conn2.sync_state.change_token = current_token

            db2.commit()
        finally:
            db2.close()
            engine2.dispose()

        return {
            "status": "queued",
            "files_queued": files_queued,
            "files_deleted": files_deleted,
        }

    except Exception as exc:
        logger.error("Incremental sync failed for %s: %s", connector_id, exc, exc_info=True)
        try:
            engine3, db3 = _get_sync_db()
            conn3 = db3.get(Connector, connector_id)
            if conn3:
                conn3.status = "error"
                conn3.error_message = str(exc)
                if conn3.sync_state:
                    conn3.sync_state.last_sync_status = "failed"
                    conn3.sync_state.last_sync_error = str(exc)
                db3.commit()
            db3.close()
            engine3.dispose()
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=RETRY_DELAY * (2 ** self.request.retries))


# ── Phase 10: Delete Handling ─────────────────────────────────────────────────

@celery_app.task(
    bind=True,
    name="connector_tasks.delete_connector_file_task",
    max_retries=3,
    acks_late=True,
)
def delete_connector_file_task(self, connector_id: str, remote_file_id: str) -> bool:
    """
    Handle a file deletion event from the remote source.

    Steps:
    1. Find the ConnectorFile row
    2. Get the linked document_id
    3. Delete vectors from Qdrant (via document_cleanup service)
    4. Delete the Document row
    5. Mark ConnectorFile as deleted
    """
    from sqlalchemy import select
    from db.models.connector import ConnectorFile

    engine, db = _get_sync_db()
    try:
        file_row = db.execute(
            select(ConnectorFile).where(
                ConnectorFile.connector_id == connector_id,
                ConnectorFile.remote_file_id == remote_file_id,
            )
        ).scalar_one_or_none()

        if not file_row:
            logger.info("File %s not tracked in connector %s — no deletion needed", remote_file_id, connector_id)
            return True

        document_id = file_row.document_id

        if document_id:
            from services.document_cleanup import delete_document_completely
            delete_document_completely(document_id, db)

        file_row.sync_status = "deleted"
        file_row.document_id = None
        db.commit()

        logger.info(
            "Deleted file %s (document %s) from connector %s",
            remote_file_id, document_id, connector_id
        )
        return True

    except Exception as exc:
        logger.error("delete_connector_file_task failed: %s", exc, exc_info=True)
        try:
            db.close()
            engine.dispose()
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=RETRY_DELAY)
    finally:
        try:
            db.close()
            engine.dispose()
        except Exception:
            pass


# ── Phase 11: Update Handling ─────────────────────────────────────────────────
# Updates are handled by sync_connector_file_task with force=True in the pipeline.
# The existing pipeline's idempotency logic (ingest_manifest) handles re-indexing.

__all__ = [
    "sync_connector_file_task",
    "sync_connector_full_task",
    "sync_connector_incremental_task",
    "delete_connector_file_task",
]
