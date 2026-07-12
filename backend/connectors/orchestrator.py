import logging
import asyncio
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from connectors.registry import ConnectorRegistry
from connectors.base.capabilities import Capability
from db.models.connector import Connector, ConnectorFile, ConnectorSyncState

logger = logging.getLogger(__name__)

class ConnectorOrchestrator:
    """
    Drives the sync loops using the capability-aware ConnectorRegistry.
    Dispatches Celery tasks to process individual files.
    """

    @classmethod
    def run_full_sync(cls, db: Session, connector: Connector, access_token: str) -> None:
        """
        Discovers all files via adapter.full_sync() and dispatches one task per file.
        """
        # Delayed import to avoid circular dependency with celery
        from connectors.tasks import download_and_enqueue_task

        adapter_class = ConnectorRegistry.get(connector.provider)
        adapter = adapter_class()
        
        # Instantiate an event loop just for discovery
        async def _run():
            await adapter.authenticate({"access_token": access_token})
            
            # Persist sync state
            if connector.sync_state:
                connector.sync_state.last_sync_started_at = datetime.now(timezone.utc)
                connector.sync_state.last_sync_mode = "full"
                connector.sync_state.last_sync_status = "running"
            connector.status = "syncing"
            db.commit()

            discovered_count = 0
            async for file_meta in adapter.full_sync():
                # Persist to DB
                file_row = db.query(ConnectorFile).filter_by(
                    connector_id=connector.id,
                    remote_file_id=file_meta.external_id
                ).first()
                
                if not file_row:
                    file_row = ConnectorFile(
                        connector_id=connector.id,
                        remote_file_id=file_meta.external_id,
                        remote_file_name=file_meta.name,
                        sync_status="syncing"
                    )
                    db.add(file_row)
                else:
                    file_row.remote_file_name = file_meta.name
                    file_row.sync_status = "syncing"
                
                db.commit()
                
                # Dispatch celery task
                download_and_enqueue_task.delay(
                    connector_id=connector.id,
                    remote_file_id=file_meta.external_id,
                    access_token=access_token,
                    original_filename=file_meta.name,
                    mime_type=file_meta.mime_type
                )
                discovered_count += 1
            
            # Fetch change token if supported
            capabilities = ConnectorRegistry.capabilities_of(connector.provider)
            if Capability.INCREMENTAL_SYNC in capabilities and connector.sync_state:
                try:
                    connector.sync_state.change_token = await adapter.get_initial_change_token()
                except Exception as e:
                    logger.warning(f"Could not get initial change token for {connector.id}: {e}")

            if connector.sync_state:
                connector.sync_state.last_sync_status = "completed"
                connector.sync_state.last_sync_completed_at = datetime.now(timezone.utc)
            connector.status = "connected"
            db.commit()
            
            logger.info(f"Full sync complete for {connector.id}. Discovered {discovered_count} files.")

        asyncio.run(_run())


    @classmethod
    def run_incremental_sync(cls, db: Session, connector: Connector, access_token: str) -> None:
        """
        Discovers new/modified files via adapter.incremental_sync() and handles deletions.
        """
        from connectors.tasks import download_and_enqueue_task
        from connectors.base.sync import SyncCursor
        
        adapter_class = ConnectorRegistry.get(connector.provider)
        adapter = adapter_class()
        
        capabilities = ConnectorRegistry.capabilities_of(connector.provider)
        if Capability.INCREMENTAL_SYNC not in capabilities:
            logger.error(f"Connector {connector.provider} does not support incremental sync.")
            return

        async def _run():
            await adapter.authenticate({"access_token": access_token})
            
            if connector.sync_state:
                connector.sync_state.last_sync_started_at = datetime.now(timezone.utc)
                connector.sync_state.last_sync_mode = "incremental"
                connector.sync_state.last_sync_status = "running"
            connector.status = "syncing"
            db.commit()

            token = connector.sync_state.change_token if connector.sync_state else None
            cursor = SyncCursor(token=token)
            
            discovered_count = 0
            async for change in adapter.incremental_sync(cursor):
                if change.change_type == "deleted":
                    # Mark deleted locally or dispatch a delete task
                    file_row = db.query(ConnectorFile).filter_by(
                        connector_id=connector.id,
                        remote_file_id=change.file_id
                    ).first()
                    if file_row:
                        file_row.sync_status = "deleted"
                        db.commit()
                else:
                    if change.file_metadata:
                        file_meta = change.file_metadata
                        # Persist to DB
                        file_row = db.query(ConnectorFile).filter_by(
                            connector_id=connector.id,
                            remote_file_id=file_meta.external_id
                        ).first()
                        
                        if not file_row:
                            file_row = ConnectorFile(
                                connector_id=connector.id,
                                remote_file_id=file_meta.external_id,
                                remote_file_name=file_meta.name,
                                sync_status="syncing"
                            )
                            db.add(file_row)
                        else:
                            file_row.remote_file_name = file_meta.name
                            file_row.sync_status = "syncing"
                        
                        db.commit()
                        
                        # Dispatch celery task
                        download_and_enqueue_task.delay(
                            connector_id=connector.id,
                            remote_file_id=file_meta.external_id,
                            access_token=access_token,
                            original_filename=file_meta.name,
                            mime_type=file_meta.mime_type
                        )
                        discovered_count += 1
            
            if cursor.token and connector.sync_state:
                connector.sync_state.change_token = cursor.token

            if connector.sync_state:
                connector.sync_state.last_sync_status = "completed"
                connector.sync_state.last_sync_completed_at = datetime.now(timezone.utc)
            connector.status = "connected"
            db.commit()
            
            logger.info(f"Incremental sync complete for {connector.id}. Processed {discovered_count} modified files.")

        asyncio.run(_run())
