"""
services/ingestion_orchestrator.py

The bridge between the connector layer and the existing ingestion pipeline.

This module is the ONLY new code that interacts with the existing pipeline.
It:
  1. Downloads a file from a connector (via ConnectorManager)
  2. Writes it to a temporary file
  3. Creates an IngestionJob row (reusing existing model)
  4. Calls run_ingestion_job() (reusing existing task)
  5. Updates ConnectorFile with the resulting document_id

The orchestrator does NOT:
  - OCR (handled by existing pipeline)
  - Chunk (handled by existing pipeline)
  - Embed (handled by existing pipeline)
  - Index to Qdrant (handled by existing pipeline)

Following the Open/Closed Principle: the existing pipeline is the black box.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from db.models.connector import Connector, ConnectorCredential, ConnectorFile
from db.models.document import Document
from db.models.ingestion import IngestionJob

logger = logging.getLogger(__name__)


def _get_sync_db() -> tuple:
    """Synchronous DB session for use in Celery worker processes."""
    cfg = get_settings()
    engine = create_engine(
        cfg.database.sync_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    return engine, factory()


def orchestrate_file_ingestion(
    connector_id: str,
    remote_file_id: str,
    access_token: str,
) -> Optional[str]:
    """
    Download a single remote file and push it through the existing ingestion pipeline.

    This is called synchronously from a Celery worker task.

    Parameters
    ----------
    connector_id : str
        ID of the Connector row.
    remote_file_id : str
        The provider-specific file ID (e.g., Google Drive file ID).
    access_token : str
        Valid access token for the connector's provider.

    Returns
    -------
    str | None
        The document_id of the newly indexed Document, or None on failure.
    """
    engine, db = _get_sync_db()
    tmp_dir: Optional[str] = None

    try:
        # Load connector and its file record
        connector: Optional[Connector] = db.get(Connector, connector_id)
        if not connector:
            logger.error("Connector %s not found", connector_id)
            return None

        # Get or create ConnectorFile row
        file_row: Optional[ConnectorFile] = db.execute(
            select(ConnectorFile).where(
                ConnectorFile.connector_id == connector_id,
                ConnectorFile.remote_file_id == remote_file_id,
            )
        ).scalar_one_or_none()

        if not file_row:
            file_row = ConnectorFile(
                connector_id=connector_id,
                remote_file_id=remote_file_id,
                sync_status="syncing",
            )
            db.add(file_row)
            db.flush()
        else:
            file_row.sync_status = "syncing"
            db.flush()

        db.commit()

        # ── Download file from provider ──────────────────────────────────────
        from connectors.manager import ConnectorManager
        manager = ConnectorManager(connector.provider)

        logger.info(
            "Downloading file %s from connector %s (%s)",
            remote_file_id, connector_id, connector.provider
        )

        # Use asyncio.run to call the async download from sync context
        import asyncio

        async def _download():
            return await manager.download_file(access_token, remote_file_id)

        content_bytes, suggested_filename = asyncio.run(_download())
        logger.info(
            "Downloaded '%s' (%d bytes)", suggested_filename, len(content_bytes)
        )

        # Update file row with metadata
        file_row.remote_file_name = suggested_filename
        file_row.sync_status = "syncing"

        # ── Write to temp file ───────────────────────────────────────────────
        tmp_dir = tempfile.mkdtemp(prefix="connector_")
        safe_filename = Path(suggested_filename).name
        tmp_path = Path(tmp_dir) / safe_filename

        with open(tmp_path, "wb") as f:
            f.write(content_bytes)

        # ── Create IngestionJob (reusing existing model) ─────────────────────
        job = IngestionJob(
            source_path_or_url=suggested_filename,
            source_type=_infer_mime(safe_filename),
            status="queued",
            user_id=connector.user_id,
            submitted_by=connector.user_id,
            config=json.dumps({
                "connector_id": connector_id,
                "remote_file_id": remote_file_id,
            }),
        )
        db.add(job)
        db.flush()
        job_id = job.id

        # Save the blob so the existing ingestion task can find it
        from services.blob_storage import get_blob_storage
        blob_svc = get_blob_storage()
        blob_path = blob_svc.save(
            content_bytes,
            safe_filename,
            job_id,
            user_id=connector.user_id,
        )
        job.blob_path = blob_path
        db.commit()

        # Update file row with job reference
        file_row.ingestion_job_id = job_id

        # ── Call existing ingestion pipeline ─────────────────────────────────
        from tasks.ingestion_tasks import run_ingestion_job
        run_ingestion_job(job_id)

        # ── Refresh job status ────────────────────────────────────────────────
        db.expire(job)
        db.refresh(job)

        if job.status == "completed":
            # Find the document that was created
            doc = db.execute(
                select(Document).where(
                    Document.ingestion_job_id == job_id,
                    Document.user_id == connector.user_id,
                )
            ).scalar_one_or_none()

            document_id = doc.id if doc else None

            file_row.sync_status = "indexed"
            file_row.document_id = document_id
            file_row.last_synced_at = datetime.now(timezone.utc)
            db.commit()

            logger.info(
                "File %s indexed as document %s via connector %s",
                remote_file_id, document_id, connector_id,
            )
            return document_id
        else:
            file_row.sync_status = "failed"
            file_row.sync_error = job.error_message or "Ingestion failed"
            file_row.retry_count += 1
            db.commit()
            logger.error(
                "Ingestion failed for file %s: %s",
                remote_file_id, job.error_message
            )
            return None

    except Exception as exc:
        logger.error(
            "orchestrate_file_ingestion failed for %s: %s",
            remote_file_id, exc, exc_info=True,
        )
        try:
            if file_row:
                file_row.sync_status = "failed"
                file_row.sync_error = str(exc)
                file_row.retry_count += 1
                db.commit()
        except Exception:
            pass
        return None

    finally:
        if tmp_dir and Path(tmp_dir).exists():
            try:
                shutil.rmtree(tmp_dir)
            except Exception as e:
                logger.warning("Failed to clean temp dir %s: %s", tmp_dir, e)
        try:
            db.close()
            engine.dispose()
        except Exception:
            pass


def _infer_mime(filename: str) -> str:
    """Infer a MIME type from filename extension."""
    ext = Path(filename).suffix.lower()
    return {
        ".pdf": "application/pdf",
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".csv": "text/csv",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".doc": "application/msword",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }.get(ext, "application/octet-stream")


__all__ = ["orchestrate_file_ingestion"]
