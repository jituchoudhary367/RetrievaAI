"""
routes/documents.py

Document catalog API — backed by the Postgres `documents` table (§1.3).

Endpoints:
  GET    /api/documents                      — paginated list
  GET    /api/documents/{id}                 — single document metadata
  DELETE /api/documents/{id}                 — remove from Qdrant + BM25 + Postgres
  GET    /api/documents/{id}/chunks          — retrieve chunk list from Qdrant
  GET    /api/documents/{id}/download        — stream original file from blob storage
"""

from __future__ import annotations

import logging
import math
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.engine import get_db
from db.models.document import Document
from security.auth import get_current_user, require_role
from services.audit import log_action
from services.blob_storage import get_blob_storage
from db.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])


# ── Response schemas ─────────────────────────────────────────────────────


class DocumentOut(BaseModel):
    id: str
    title: Optional[str]
    source: str
    source_type: str
    tags: Optional[list]
    chunk_count: int
    size_bytes: int
    quality_score: float
    blob_path: Optional[str]
    ingestion_job_id: Optional[str]
    uploaded_by: Optional[str]
    uploaded_at: str
    updated_at: str

    @classmethod
    def from_orm(cls, doc: Document) -> "DocumentOut":
        import json
        return cls(
            id=doc.id,
            title=doc.title,
            source=doc.source,
            source_type=doc.source_type,
            tags=json.loads(doc.tags) if doc.tags else [],
            chunk_count=doc.chunk_count,
            size_bytes=doc.size_bytes,
            quality_score=doc.quality_score,
            blob_path=doc.blob_path,
            ingestion_job_id=doc.ingestion_job_id,
            uploaded_by=doc.uploaded_by,
            uploaded_at=doc.uploaded_at.isoformat(),
            updated_at=doc.updated_at.isoformat(),
        )


class DocumentListResponse(BaseModel):
    items: List[DocumentOut]
    total: int
    page: int
    page_size: int
    total_pages: int


class ChunkOut(BaseModel):
    chunk_id: str
    text: str
    chunk_index: int
    score: Optional[float] = None


# ── Routes ───────────────────────────────────────────────────────────────


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    source_type: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None, description="Filter by title/source substring"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    query = select(Document).where(Document.tenant_id == current_user.tenant_id)
    count_q = select(func.count()).select_from(Document).where(Document.tenant_id == current_user.tenant_id)

    if source_type:
        query = query.where(Document.source_type == source_type)
        count_q = count_q.where(Document.source_type == source_type)

    if q:
        like = f"%{q}%"
        query = query.where(
            Document.title.ilike(like) | Document.source.ilike(like)
        )
        count_q = count_q.where(
            Document.title.ilike(like) | Document.source.ilike(like)
        )

    total = (await db.execute(count_q)).scalar_one()
    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(Document.uploaded_at.desc()).offset(offset).limit(page_size)
    )
    docs = result.scalars().all()

    return DocumentListResponse(
        items=[DocumentOut.from_orm(d) for d in docs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total else 0,
    )


@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentOut:
    doc = await _get_doc_or_404(db, document_id, current_user.tenant_id)
    return DocumentOut.from_orm(doc)


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: str,
    current_user: User = Depends(require_role("TENANT_ADMIN", "EDITOR")),
    db: AsyncSession = Depends(get_db),
) -> None:
    doc = await _get_doc_or_404(db, document_id, current_user.tenant_id)

    # Remove from Qdrant
    try:
        from pipeline.indexer import Indexer  # noqa: PLC0415
        indexer = Indexer()
        indexer.remove_document(document_id)
    except Exception as exc:
        logger.error("Qdrant/BM25 delete failed for doc %s: %s", document_id, exc)

    # Remove blob
    if doc.blob_path:
        try:
            get_blob_storage().delete(doc.blob_path)
        except Exception as exc:
            logger.warning("Blob delete failed for doc %s: %s", document_id, exc)

    await db.delete(doc)
    import asyncio
    asyncio.create_task(log_action(
        tenant_id=current_user.tenant_id,
        actor_user_id=current_user.id,
        action="document.delete",
        target=f"document:{document_id}",
        detail={"title": doc.title, "source": doc.source},
    ))


@router.get("/{document_id}/chunks", response_model=List[ChunkOut])
async def get_document_chunks(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ChunkOut]:
    """Return chunks for a document from Qdrant."""
    await _get_doc_or_404(db, document_id, current_user.tenant_id)

    try:
        from qdrant_client import QdrantClient  # noqa: PLC0415
        from qdrant_client.http.models import Filter, FieldCondition, MatchValue  # noqa: PLC0415
        from app.config import get_settings  # noqa: PLC0415
        cfg = get_settings()
        client = QdrantClient(host=cfg.qdrant.host, port=cfg.qdrant.port)
        points, _ = client.scroll(
            collection_name=cfg.qdrant.collection_name,
            scroll_filter=Filter(must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]),
            limit=200,
            with_payload=True,
            with_vectors=False,
        )
        return [
            ChunkOut(
                chunk_id=str(p.id),
                text=p.payload.get("text", ""),
                chunk_index=p.payload.get("chunk_index", 0),
            )
            for p in points
        ]
    except Exception as exc:
        logger.error("Failed to fetch chunks for doc %s: %s", document_id, exc)
        raise HTTPException(status_code=503, detail="Could not retrieve chunks from vector store")


@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Stream the original file from blob storage."""
    doc = await _get_doc_or_404(db, document_id, current_user.tenant_id)

    if not doc.blob_path:
        raise HTTPException(status_code=404, detail="Original file not available (no blob)")

    blob = get_blob_storage()
    try:
        data = blob.load(doc.blob_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found in blob storage")

    import io
    filename = doc.title or doc.source.split("/")[-1]

    def _iter():
        yield data

    return StreamingResponse(
        _iter(),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Helpers ───────────────────────────────────────────────────────────────


async def _get_doc_or_404(db: AsyncSession, document_id: str, tenant_id: str) -> Document:
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.tenant_id == tenant_id,
        )
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc
