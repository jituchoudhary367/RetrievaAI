import asyncio
import json
import logging
import tempfile
from pathlib import Path
from typing import Optional

from tasks.celery_app import celery_app
from tasks.connector_tasks import _get_sync_db, _get_fresh_token_sync
from db.models.connector import Connector, ConnectorFile
from db.models.ingestion import IngestionJob
from connectors.registry import ConnectorRegistry
from connectors.orchestrator import ConnectorOrchestrator
from connectors.base.payload import IngestionTaskPayload
from services.blob_storage import get_blob_storage
from tasks.ingestion_tasks import run_ingestion_job

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY = 60

@celery_app.task(bind=True, max_retries=1, acks_late=True)
def discover_files_task(self, connector_id: str, is_incremental: bool = False) -> dict:
    """
    Wraps the orchestrator sync loops.
    """
    engine, db = _get_sync_db()
    try:
        connector = db.get(Connector, connector_id)
        if not connector:
            return {"status": "error", "reason": "connector_not_found"}

        access_token = _get_fresh_token_sync(db, connector)
        
        if is_incremental:
            ConnectorOrchestrator.run_incremental_sync(db, connector, access_token)
        else:
            ConnectorOrchestrator.run_full_sync(db, connector, access_token)
            
        return {"status": "success"}
    except Exception as exc:
        logger.error(f"discover_files_task failed for {connector_id}: {exc}")
        raise self.retry(exc=exc, countdown=30)
    finally:
        db.close()
        engine.dispose()

@celery_app.task(bind=True, max_retries=MAX_RETRIES, default_retry_delay=RETRY_DELAY, acks_late=True)
def download_and_enqueue_task(self, connector_id: str, remote_file_id: str, access_token: str, original_filename: str, mime_type: Optional[str]) -> Optional[str]:
    """
    Per-file atomic task. Fetches the adapter, calls download_file(), saves to blob storage,
    builds IngestionTaskPayload, creates IngestionJob, and strictly calls the existing run_ingestion_job(job_id).
    """
    engine, db = _get_sync_db()
    try:
        connector = db.get(Connector, connector_id)
        if not connector:
            logger.error("Connector %s not found — skipping file %s", connector_id, remote_file_id)
            return None

        # Fetch the adapter
        adapter_class = ConnectorRegistry.get(connector.provider)
        adapter = adapter_class()
        
        # Authenticate
        async def _download():
            await adapter.authenticate({"access_token": access_token})
            return await adapter.download_file(remote_file_id)

        content_bytes = asyncio.run(_download())
        
        # Save the blob so the existing ingestion task can find it
        blob_svc = get_blob_storage()
        # Generate a mock job_id for blob storage before job creation to keep existing pattern
        import uuid
        temp_job_id = str(uuid.uuid4())
        safe_filename = Path(original_filename).name if original_filename else remote_file_id
        
        blob_path = blob_svc.save(
            content_bytes,
            safe_filename,
            temp_job_id,
            user_id=connector.user_id,
        )

        # Build strict payload
        payload = IngestionTaskPayload(
            connector_id=connector_id,
            connector_file_id=remote_file_id,
            external_id=remote_file_id,
            org_id=connector.user_id,
            source_provider=connector.provider,
            file_bytes_ref=blob_path,
            original_filename=original_filename or remote_file_id,
            mime_type=mime_type
        )

        # Create IngestionJob using the existing model
        job = IngestionJob(
            id=temp_job_id,
            source_path_or_url=safe_filename,
            source_type=mime_type or "application/octet-stream",
            status="queued",
            user_id=connector.user_id,
            submitted_by=connector.user_id,
            blob_path=blob_path,
            config=payload.model_dump_json(),
        )
        db.add(job)
        
        # Link job to ConnectorFile
        file_row = db.query(ConnectorFile).filter_by(
            connector_id=connector_id,
            remote_file_id=remote_file_id
        ).first()
        
        if file_row:
            file_row.ingestion_job_id = job.id
            file_row.sync_status = "syncing"
        
        db.commit()

        # Call existing unmodified ingestion entrypoint
        run_ingestion_job(job.id)
        
        return job.id

    except Exception as exc:
        logger.error("download_and_enqueue_task failed: %s", exc, exc_info=True)
        # Mark failed locally
        try:
            file_row = db.query(ConnectorFile).filter_by(connector_id=connector_id, remote_file_id=remote_file_id).first()
            if file_row:
                file_row.sync_status = "failed"
                file_row.sync_error = str(exc)
                file_row.retry_count += 1
                db.commit()
        except:
            pass
        raise self.retry(exc=exc, countdown=RETRY_DELAY * (2 ** self.request.retries))
    finally:
        db.close()
        engine.dispose()

@celery_app.task(bind=True, max_retries=1, acks_late=True)
def sync_connector_task(self, connector_id: str, force_full: bool = False) -> dict:
    """
    Top-level entrypoint that decides whether to run a full or incremental sync.
    """
    engine, db = _get_sync_db()
    try:
        connector = db.get(Connector, connector_id)
        if not connector:
            return {"status": "error", "reason": "connector_not_found"}

        capabilities = ConnectorRegistry.capabilities_of(connector.provider)
        
        is_incremental = False
        if not force_full and Capability.INCREMENTAL_SYNC in capabilities:
            if connector.sync_state and connector.sync_state.change_token:
                is_incremental = True

        discover_files_task.delay(connector_id, is_incremental=is_incremental)
        return {"status": "success", "mode": "incremental" if is_incremental else "full"}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=10)
    finally:
        db.close()
        engine.dispose()

@celery_app.task(bind=True, max_retries=2, acks_late=True)
def refresh_token_task(self, connector_id: str) -> dict:
    """
    Background token refreshment logic using the adapter's refresh_token().
    """
    engine, db = _get_sync_db()
    try:
        connector = db.get(Connector, connector_id)
        if not connector or not connector.credential or not connector.credential.refresh_token:
            return {"status": "error"}

        adapter_class = ConnectorRegistry.get(connector.provider)
        adapter = adapter_class()

        async def _refresh():
            return await adapter.refresh_token(connector.credential.refresh_token)
            
        token_data = asyncio.run(_refresh())
        if token_data and "access_token" in token_data:
            connector.credential.access_token = token_data["access_token"]
            if "expires_at" in token_data:
                connector.credential.expires_at = token_data["expires_at"]
            db.commit()
            
        return {"status": "success"}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()
        engine.dispose()

@celery_app.task
def schedule_connectors_task() -> None:
    from connectors.scheduler import evaluate_and_schedule_connectors
    evaluate_and_schedule_connectors()

