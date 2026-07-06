"""
services/document_cleanup.py

Handles complete document deletion: vectors from Qdrant + Document catalog row.

Called by the connector delete task when a file is removed from the
remote source. Does NOT modify the existing ingestion pipeline.
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from db.models.document import Document

logger = logging.getLogger(__name__)


def delete_document_completely(document_id: str, db: Session) -> bool:
    """
    Delete a document from all storage layers:
      1. Qdrant vector store (all chunks for this document)
      2. BM25 sparse index (via Indexer)
      3. Document catalog row in PostgreSQL

    Parameters
    ----------
    document_id : str
        The Document.id to delete.
    db : Session
        Synchronous SQLAlchemy session.

    Returns
    -------
    bool
        True if deleted, False if document not found.
    """
    doc: Optional[Document] = db.get(Document, document_id)
    if not doc:
        logger.warning("Document %s not found for deletion", document_id)
        return False

    user_id = doc.user_id

    # 1. Delete from Qdrant (all chunks that belong to this document)
    try:
        _delete_vectors_from_qdrant(document_id, user_id)
    except Exception as exc:
        logger.error("Failed to delete vectors for document %s: %s", document_id, exc)
        # Continue anyway — we still want to clean up the DB row

    # 2. Delete from BM25 sparse index
    try:
        _delete_from_bm25(document_id, user_id)
    except Exception as exc:
        logger.warning("Failed to delete BM25 entries for document %s: %s", document_id, exc)

    # 3. Delete the Document catalog row (cascades to query_event_citations)
    db.delete(doc)
    db.commit()

    logger.info("Document %s fully deleted (user=%s)", document_id, user_id)
    return True


def _delete_vectors_from_qdrant(document_id: str, user_id: str) -> int:
    """
    Delete all Qdrant points that belong to the given document.

    Uses the 'document_id' metadata filter which is set by the indexer
    when chunks are ingested.
    """
    from pipeline.indexer import Indexer
    from qdrant_client.models import Filter, FieldCondition, MatchValue

    indexer = Indexer()
    client = indexer._client

    # Delete by document_id metadata filter
    result = client.delete(
        collection_name=indexer._collection,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id),
                )
            ]
        ),
    )

    logger.info("Deleted Qdrant vectors for document %s (result: %s)", document_id, result)
    return 0


def _delete_from_bm25(document_id: str, user_id: str) -> None:
    """
    Remove document from BM25 sparse index.

    The BM25 index is rebuilt on search, so we mark the document as deleted
    via Qdrant filter. If BM25 uses a separate data structure, extend here.
    """
    # In your current stack, BM25 is served through Qdrant sparse vectors,
    # so the Qdrant deletion above already removes BM25 vectors.
    # This function is a hook for future separate BM25 backends.
    pass


__all__ = ["delete_document_completely"]
