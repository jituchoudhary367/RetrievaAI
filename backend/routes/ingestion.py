"""
routes/ingestion.py

Async ingestion routes (§1.2).

Replaces the old blocking POST /api/ingest.

Endpoints:
  GET    /api/ingestion/jobs
  POST   /api/ingestion/jobs
  GET    /api/ingestion/jobs/{id}
  DELETE /api/ingestion/jobs/{id}
  POST   /api/ingestion/jobs/{id}/cancel
  GET    /api/ingestion/jobs/{id}/stream  (SSE logs via Redis Pub/Sub)
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, Response
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from db.engine import get_db
from db.models.ingestion import IngestionJob, IngestionJobLog
from security.auth import get_current_user, require_role
from services.audit import log_action
from services.blob_storage import get_blob_storage
from db.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ingestion", tags=["ingestion"])


# ── Response schemas ─────────────────────────────────────────────────────

class IngestionJobOut(BaseModel):
    id: str
    source_path_or_url: str
    source_type: Optional[str]
    status: str
    progress_percent: float
    chunks_total: int
    chunks_indexed: int
    error_message: Optional[str]
    submitted_by: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    created_at: str

    @classmethod
    def from_orm(cls, job: IngestionJob) -> "IngestionJobOut":
        return cls(
            id=job.id,
            source_path_or_url=job.source_path_or_url,
            source_type=job.source_type,
            status=job.status,
            progress_percent=job.progress_percent,
            chunks_total=job.chunks_total,
            chunks_indexed=job.chunks_indexed,
            error_message=job.error_message,
            submitted_by=job.submitted_by,
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            created_at=job.created_at.isoformat(),
        )

class IngestionJobListResponse(BaseModel):
    items: List[IngestionJobOut]
    total: int

class IngestionJobSubmitResponse(BaseModel):
    job_id: str
    message: str


# ── Routes ───────────────────────────────────────────────────────────────

@router.get("/jobs", response_model=IngestionJobListResponse)
async def list_jobs(
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> IngestionJobListResponse:
    q = select(IngestionJob).where(IngestionJob.user_id == current_user.id)
    if status:
        q = q.where(IngestionJob.status == status)
    
    q = q.order_by(IngestionJob.created_at.desc()).limit(limit)
    
    result = await db.execute(q)
    jobs = result.scalars().all()
    
    count_q = select(func.count()).select_from(IngestionJob).where(IngestionJob.user_id == current_user.id)
    if status:
        count_q = count_q.where(IngestionJob.status == status)
    total = (await db.execute(count_q)).scalar_one()

    return IngestionJobListResponse(
        items=[IngestionJobOut.from_orm(j) for j in jobs],
        total=total
    )

@router.post("/jobs", response_model=IngestionJobSubmitResponse, status_code=202)
async def submit_job(
    file: UploadFile = File(...),
    chunk_size: Optional[int] = Form(default=None),
    chunk_overlap: Optional[int] = Form(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> IngestionJobSubmitResponse:
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Save to blob storage
    blob_svc = get_blob_storage()
    file_bytes = await file.read()
    
    import uuid
    temp_doc_id = str(uuid.uuid4())
    blob_path = blob_svc.save(file_bytes, file.filename, temp_doc_id, user_id=current_user.id)

    # Config overrides
    config = {}
    if chunk_size: config["chunk_size"] = chunk_size
    if chunk_overlap: config["chunk_overlap"] = chunk_overlap

    job = IngestionJob(
        source_path_or_url=file.filename,
        source_type=file.content_type or "application/octet-stream",
        status="queued",
        config=json.dumps(config) if config else None,
        user_id=current_user.id,
        submitted_by=current_user.id,
        blob_path=blob_path
    )
    db.add(job)
    await db.flush()
    job_id = job.id
    await db.commit()

    # Execute task immediately in a background thread for real-time processing
    try:
        from tasks.ingestion_tasks import run_ingestion_job # type: ignore
        asyncio.create_task(asyncio.to_thread(run_ingestion_job, job_id))
    except Exception as exc:
        logger.error("Failed to start background job: %s", exc)
        job.status = "failed"
        job.error_message = "Failed to start background task"
        await db.commit()
        raise HTTPException(status_code=500, detail="Failed to start background job")

    asyncio.create_task(log_action(
        actor_user_id=current_user.id,
        action="ingestion.submit",
        target=f"job:{job_id}",
        detail={"filename": file.filename},
    ))

    return IngestionJobSubmitResponse(
        job_id=job_id,
        message="Job queued successfully"
    )

@router.get("/jobs/{job_id}", response_model=IngestionJobOut)
async def get_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> IngestionJobOut:
    result = await db.execute(
        select(IngestionJob).where(
            IngestionJob.id == job_id,
            IngestionJob.user_id == current_user.id
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return IngestionJobOut.from_orm(job)

@router.delete("/jobs/{job_id}", status_code=200)
async def delete_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        select(IngestionJob).where(
            IngestionJob.id == job_id,
            IngestionJob.user_id == current_user.id
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Delete chunks from Qdrant via Indexer
    from pipeline.indexer import Indexer
    try:
        Indexer().remove_by_source(job.source_path_or_url, user_id=current_user.id)
    except Exception as e:
        logger.error(f"Failed to delete chunks for {job_id} from vector DB: {e}")

    # Delete Document from DB
    from db.models.document import Document
    doc_result = await db.execute(
        select(Document).where(
            Document.ingestion_job_id == job_id
        )
    )
    doc = doc_result.scalar_one_or_none()
    if doc:
        await db.delete(doc)

    await db.delete(job)
    await db.commit()

@router.get("/jobs/{job_id}/chunks")
async def get_job_chunks(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    result = await db.execute(
        select(IngestionJob).where(
            IngestionJob.id == job_id,
            IngestionJob.user_id == current_user.id
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    from pipeline.indexer import QdrantIndexer
    chunks = QdrantIndexer().get_chunks_by_source_path(job.source_path_or_url)
    return chunks

@router.get("/jobs/{job_id}/metadata")
async def get_job_metadata(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from db.models.document import Document
    doc_result = await db.execute(
        select(Document).where(
            Document.ingestion_job_id == job_id,
            Document.user_id == current_user.id
        )
    )
    doc = doc_result.scalar_one_or_none()
    if not doc:
        return {}
        
    return {
        "id": doc.id,
        "title": doc.title,
        "source": doc.source,
        "source_type": doc.source_type,
        "chunk_count": doc.chunk_count,
        "size_bytes": doc.size_bytes,
        "quality_score": doc.quality_score,
        "tags": doc.tags,
        "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
        "updated_at": doc.updated_at.isoformat() if doc.updated_at else None
    }

@router.post("/jobs/{job_id}/cancel", status_code=200)
async def cancel_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(IngestionJob).where(
            IngestionJob.id == job_id,
            IngestionJob.user_id == current_user.id
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status not in ["queued", "processing"]:
        raise HTTPException(status_code=400, detail=f"Cannot cancel job in status {job.status}")
    
    # Simple cancel - mark in DB. RQ worker would need to check this periodically to stop early.
    job.status = "cancelled"
    job.completed_at = datetime.utcnow()
    await db.commit()
    return {"message": "Job marked as cancelled"}

@router.get("/jobs/{job_id}/stream")
async def stream_job_logs(
    request: Request,
    job_id: str,
    # Skipping auth dependency in SSE due to browser EventSource not supporting headers. 
    # Use a token query param if needed in production.
    db: AsyncSession = Depends(get_db),
):
    """SSE endpoint for live job logs via Redis Pub/Sub."""
    # Verify job exists
    result = await db.execute(select(IngestionJob).where(IngestionJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    async def log_generator():
        # Yield past logs first
        logs_result = await db.execute(
            select(IngestionJobLog).where(IngestionJobLog.job_id == job_id).order_by(IngestionJobLog.timestamp)
        )
        for log_row in logs_result.scalars().all():
            yield {
                "event": "log",
                "data": json.dumps({
                    "level": log_row.level,
                    "message": log_row.message,
                    "timestamp": log_row.timestamp.isoformat()
                })
            }
        
        # Subscribe to new logs if still running
        if job.status in ["queued", "processing"]:
            try:
                import redis.asyncio as redis_async # type: ignore
                cfg = get_settings()
                r = redis_async.Redis.from_url(cfg.redis.url, decode_responses=True)
                pubsub = r.pubsub()
                await pubsub.subscribe(f"ingestion:{job_id}")
                
                while True:
                    if await request.is_disconnected():
                        break
                    
                    message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                    if message:
                        # Message data is JSON string
                        yield {
                            "event": "log",
                            "data": message["data"]
                        }
                        
                        data = json.loads(message["data"])
                        if "Completed:" in data.get("message", "") or "Ingestion failed" in data.get("message", "") or "Worker error" in data.get("message", ""):
                            break
                    else:
                        # Keep-alive
                        yield {"event": "ping", "data": "ping"}
                        
            except Exception as e:
                logger.error(f"SSE error: {e}")
                yield {"event": "error", "data": str(e)}
            finally:
                if 'pubsub' in locals():
                    await pubsub.unsubscribe()
                    await pubsub.close()
                if 'r' in locals():
                    await r.aclose()

    return EventSourceResponse(log_generator())

