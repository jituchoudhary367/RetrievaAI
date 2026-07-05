"""
tasks/ingestion_tasks.py

RQ task wrapper for the ingestion pipeline (§1.2).

run_ingestion_job(job_id) is enqueued by POST /api/ingestion/jobs and
executed by the `rq worker ingestion` process.

Per §1.2:
  - Persists progress to IngestionJob row as the pipeline runs.
  - Writes one IngestionJobLog row per pipeline stage transition.
  - Publishes the same log line to Redis Pub/Sub channel
    `ingestion:{job_id}` for SSE streaming (§3.4).
  - Reads IngestionJob.config for per-job Chunker/Embedder overrides.

The task uses a synchronous DB session (psycopg2) because RQ workers
run in a regular sync Python process, not an async event loop.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import redis as redis_lib
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from db.base import Base  # ensures all models are registered
from db.models.ingestion import IngestionJob, IngestionJobLog
from db.models.document import Document
from services.blob_storage import get_blob_storage
from pipeline.ingest import IngestionPipeline
from pipeline.chunker import Chunker
from pipeline.embedder import Embedder

logger = logging.getLogger(__name__)

_REDIS_CHANNEL_PREFIX = "ingestion:"


def _get_sync_session() -> tuple:
    """Return a (engine, Session) pair for the RQ worker process."""
    cfg = get_settings()
    engine = create_engine(
        cfg.database.sync_url, 
        pool_pre_ping=True,
        pool_size=cfg.database.pool_size,
        max_overflow=cfg.database.max_overflow
    )
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    return engine, factory()


def _get_redis() -> Optional[redis_lib.Redis]:
    try:
        cfg = get_settings()
        return redis_lib.Redis.from_url(cfg.redis.url, decode_responses=True)
    except Exception as exc:
        logger.warning("Could not connect to Redis for pub/sub: %s", exc)
        return None


def _log_and_publish(
    db: Session,
    redis: Optional[redis_lib.Redis],
    job_id: str,
    level: str,
    message: str,
) -> None:
    """Write an IngestionJobLog row and publish to Redis Pub/Sub."""
    row = IngestionJobLog(
        job_id=job_id,
        timestamp=datetime.now(timezone.utc),
        level=level,
        message=message,
    )
    db.add(row)
    db.flush()

    if redis is not None:
        try:
            payload = json.dumps({
                "job_id": job_id,
                "level": level,
                "message": message,
                "timestamp": row.timestamp.isoformat(),
            })
            redis.publish(f"{_REDIS_CHANNEL_PREFIX}{job_id}", payload)
        except Exception as exc:  # noqa: BLE001
            logger.debug("Redis publish failed for job %s: %s", job_id, exc)


def run_ingestion_job(job_id: str) -> None:
    """
    RQ task — runs in the worker process.

    Fetches the IngestionJob row, runs the pipeline with per-job config
    overrides, updates the job row with progress, and writes log entries.
    """
    engine, db = _get_sync_session()
    redis = _get_redis()
    settings = get_settings()

    try:
        job: Optional[IngestionJob] = db.get(IngestionJob, job_id)
        if job is None:
            logger.error("IngestionJob %s not found in DB.", job_id)
            return

        # Mark as processing
        job.status = "processing"
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        _log_and_publish(db, redis, job_id, "INFO", "Job started — loading configuration")
        db.commit()

        # Parse per-job config overrides
        config: Dict[str, Any] = {}
        if job.config:
            try:
                config = json.loads(job.config)
            except json.JSONDecodeError:
                logger.warning("Invalid config JSON for job %s", job_id)

        chunk_size = config.get("chunk_size", settings.chunking.chunk_size)
        chunk_overlap = config.get("chunk_overlap", settings.chunking.chunk_overlap)
        embedding_model = config.get("embedding_model", settings.embedding.model_name)

        # Build pipeline with per-job overrides
        chunker = Chunker()
        chunker._cfg = chunker._cfg.model_copy(update={
            "chunk_size": chunk_size, 
            "chunk_overlap": chunk_overlap
        })
        
        embedder = Embedder()
        embedder._cfg = embedder._cfg.model_copy(update={
            "model_name": embedding_model
        })
        pipeline = IngestionPipeline(chunker=chunker, embedder=embedder)

        # Determine source
        source_path = Path(job.source_path_or_url)
        blob_storage = get_blob_storage()

        # If it's a blob path, resolve from blob storage
        if not source_path.exists() and job.blob_path:
            # Write blob to a temp file for the pipeline
            import tempfile  # noqa: PLC0415
            import shutil  # noqa: PLC0415
            blob_bytes = blob_storage.load(job.blob_path, user_id=job.user_id)
            tmp_dir = tempfile.mkdtemp()
            # Try to get the original filename from source_path_or_url
            original_filename = Path(job.source_path_or_url).name
            if not original_filename:
                suffix = Path(job.source_path_or_url).suffix or ".bin"
                original_filename = f"document{suffix}"
            
            tmp_path = Path(tmp_dir) / original_filename
            with open(tmp_path, "wb") as tmp_file:
                tmp_file.write(blob_bytes)
            source_path = tmp_path

        _log_and_publish(db, redis, job_id, "INFO", f"Extracting: {job.source_path_or_url}")
        db.commit()

        if not source_path.exists():
            raise FileNotFoundError(f"Source not found: {source_path}")

        # Run ingestion
        t_start = time.monotonic()
        report = pipeline.ingest_path(source_path, user_id=job.user_id, force=True)
        elapsed = time.monotonic() - t_start

        # Update job with results
        total_indexed = sum(r.num_chunks for r in report.results if r.status == "indexed")
        job.chunks_indexed = total_indexed
        job.chunks_total = total_indexed
        job.progress_percent = 100.0

        if report.failed > 0 and report.indexed == 0:
            job.status = "failed"
            error_msgs = [r.error for r in report.results if r.error]
            job.error_message = "; ".join(error_msgs[:3])
            _log_and_publish(db, redis, job_id, "ERROR", f"Ingestion failed: {job.error_message}")
        else:
            job.status = "completed"
            _log_and_publish(
                db, redis, job_id, "INFO",
                f"Completed: {total_indexed} chunks indexed in {elapsed:.1f}s"
            )

        job.completed_at = datetime.now(timezone.utc)

        # Upsert Document catalog row (§1.3)
        existing = db.execute(
            select(Document).where(
                Document.source == job.source_path_or_url,
                Document.user_id == job.user_id
            )
        ).scalar_one_or_none()

        if existing:
            existing.chunk_count = total_indexed
        else:
            doc = Document(
                title=Path(job.source_path_or_url).name,
                source=job.source_path_or_url,
                source_type=job.source_type or "unknown",
                chunk_count=total_indexed,
                ingestion_job_id=job_id,
                user_id=job.user_id,
                uploaded_by=job.submitted_by,
                blob_path=job.blob_path,
            )
            db.add(doc)

        db.commit()

    except Exception as exc:  # noqa: BLE001
        logger.error("IngestionJob %s crashed: %s", job_id, exc, exc_info=True)
        try:
            if job is not None:
                job.status = "failed"
                job.error_message = str(exc)
                job.completed_at = datetime.now(timezone.utc)
                db.commit()
                _log_and_publish(db, redis, job_id, "ERROR", f"Crashed: {job.error_message}")
        except Exception:
            logger.exception("Failed to update job status after crash.")
    finally:
        # Clean up temp directory if it was created for blob download
        if 'tmp_dir' in locals():
            try:
                shutil.rmtree(tmp_dir)
            except Exception as e:
                logger.warning("Failed to clean up temp dir %s: %s", tmp_dir, e)
        db.close()
        engine.dispose()


__all__ = ["run_ingestion_job"]
