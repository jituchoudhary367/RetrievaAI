"""
pipeline/indexer.py

Dual-vector index writer: keeps a dense Qdrant vector and a sparse vector
in sync for every write operation using Qdrant Native Hybrid Search.

Exports:
  QdrantIndexer  — upserts/deletes dual-vector chunks in Qdrant
  Indexer        — facade that calls QdrantIndexer
  IndexingError  — domain exception
"""

from __future__ import annotations

import logging
import math
import threading
import pickle
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from cachetools import LRUCache

from app.config import QdrantSettings, get_settings
from app.models import Chunk

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Domain error
# ---------------------------------------------------------------------------

class IndexingError(Exception):
    """Raised when an indexing operation fails."""







class QdrantIndexer:
    """
    Upserts and deletes chunks from a Qdrant vector collection.

    Creates the collection with HNSW parameters from ``QdrantSettings`` if it
    does not already exist.
    """

    def __init__(self, settings: Optional[QdrantSettings] = None) -> None:
        self._cfg: QdrantSettings = settings or get_settings().qdrant
        self._client = None  # Lazy init to avoid import at module load
        self._client_lock = threading.Lock()

    # ------------------------------------------------------------------
    # Client
    # ------------------------------------------------------------------

    def _get_client(self) -> object:
        if self._client is not None:
            return self._client
        with self._client_lock:
            if self._client is not None:
                return self._client
            try:
                from qdrant_client import QdrantClient  # noqa: PLC0415
                from qdrant_client.http.models import Distance, VectorParams, HnswConfigDiff  # noqa: PLC0415
            except ImportError as exc:
                raise ImportError(
                    "qdrant-client is required. Install it with: pip install qdrant-client"
                ) from exc

        cfg = self._cfg
        self._client = QdrantClient(
            host=cfg.host,
            port=cfg.port,
            grpc_port=cfg.grpc_port,
            prefer_grpc=cfg.prefer_grpc,
            api_key=cfg.api_key,
            https=cfg.https,
            timeout=cfg.timeout,
        )
        self._ensure_collection(self._client, Distance, VectorParams, HnswConfigDiff)
        return self._client

    def _ensure_collection(
        self, client: object, Distance: object, VectorParams: object, HnswConfigDiff: object
    ) -> None:
        from qdrant_client.http.models import Distance as Dist, VectorParams as VP, HnswConfigDiff as HNSW, SparseVectorParams  # noqa: PLC0415
        cfg = self._cfg
        collections = [c.name for c in client.get_collections().collections]
        
        # Schema migration check: if collection exists, ensure it is dual-vector.
        if cfg.collection_name in collections:
            col_info = client.get_collection(cfg.collection_name)
            if not getattr(col_info.config.params, "sparse_vectors", None):
                logger.warning(
                    "Collection '%s' is missing sparse_vectors schema. "
                    "Recreating collection to support Native Hybrid Search.",
                    cfg.collection_name
                )
                client.delete_collection(cfg.collection_name)
            else:
                return

        distance_map = {
            "Cosine": Dist.COSINE,
            "Euclid": Dist.EUCLID,
            "Dot": Dist.DOT,
        }
        distance = distance_map.get(cfg.distance_metric, Dist.COSINE)

        client.create_collection(
            collection_name=cfg.collection_name,
            vectors_config={
                "text-dense": VP(size=cfg.vector_size, distance=distance)
            },
            sparse_vectors_config={
                "text-sparse": SparseVectorParams()
            },
            hnsw_config=HNSW(ef_construct=cfg.hnsw_ef_construct, m=cfg.hnsw_m),
        )
        logger.info(
            "Created Qdrant dual-vector collection '%s' (dim=%d, distance=%s).",
            cfg.collection_name,
            cfg.vector_size,
            cfg.distance_metric,
        )

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def upsert_chunks(self, chunks: List[Chunk]) -> int:
        """Upsert *chunks* into Qdrant. Returns number of points upserted."""
        if not chunks:
            return 0
        try:
            from qdrant_client.http.models import PointStruct, SparseVector  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "qdrant-client is required. Install it with: pip install qdrant-client"
            ) from exc

        client = self._get_client()
        points = []
        for chunk in chunks:
            if chunk.embedding is None:
                logger.warning("Chunk %s has no embedding; skipping upsert.", chunk.chunk_id)
                continue
            
            sparse_emb = chunk.metadata.pop("sparse_embedding", None)
            
            payload = {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "user_id": chunk.user_id,
                "text": chunk.text,
                "chunk_index": chunk.chunk_index,
                **chunk.metadata,
            }

            dense_emb = chunk.embedding.tolist() if hasattr(chunk.embedding, "tolist") else chunk.embedding
            vector_dict = {
                "text-dense": dense_emb
            }
            if sparse_emb:
                vector_dict["text-sparse"] = SparseVector(
                    indices=sparse_emb.indices.tolist() if hasattr(sparse_emb.indices, "tolist") else list(sparse_emb.indices),
                    values=sparse_emb.values.tolist() if hasattr(sparse_emb.values, "tolist") else list(sparse_emb.values)
                )

            points.append(
                PointStruct(
                    id=chunk.chunk_id,
                    vector=vector_dict,
                    payload=payload,
                )
            )

        if not points:
            return 0

        batch_size = 256
        for i in range(0, len(points), batch_size):
            client.upsert(
                collection_name=self._cfg.collection_name,
                points=points[i:i + batch_size],
                wait=True,
            )
        logger.info("Upserted %d dual-vector point(s) into Qdrant.", len(points))
        return len(points)

    def search(
        self,
        query_vector: List[float],
        top_k: int = 20,
        query_filter: object = None,
    ) -> List[object]:
        """Dense vector search. Returns raw ``ScoredPoint`` objects."""
        client = self._get_client()
        return client.search(
            collection_name=self._cfg.collection_name,
            query_vector=query_vector,
            limit=top_k,
            query_filter=query_filter,
            with_payload=True,
        )

    def delete_by_document_id(self, document_id: str) -> None:
        """Delete all points belonging to *document_id*."""
        try:
            from qdrant_client.http.models import Filter, FieldCondition, MatchValue  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "qdrant-client is required. Install it with: pip install qdrant-client"
            ) from exc

        client = self._get_client()
        
        client.delete(
            collection_name=self._cfg.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(key="document_id", match=MatchValue(value=document_id)),
                ]
            ),
            wait=True,
        )
        logger.info("Deleted all points for document_id=%s from Qdrant.", document_id)

    def delete_by_source_path(self, source_path: str) -> None:
        """Delete all points belonging to a specific *source_path*."""
        try:
            from qdrant_client.http.models import Filter, FieldCondition, MatchValue  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "qdrant-client is required. Install it with: pip install qdrant-client"
            ) from exc

        client = self._get_client()
        
        client.delete(
            collection_name=self._cfg.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(key="source_path", match=MatchValue(value=source_path)),
                ]
            ),
            wait=True,
        )
        logger.info("Deleted all points for source_path=%s from Qdrant.", source_path)


    def get_chunks_by_source_path(self, source_path: str, limit: int = 100) -> List[dict]:
        """Fetch chunks for a specific source path from Qdrant (for UI display)."""
        try:
            from qdrant_client.http.models import Filter, FieldCondition, MatchValue  # noqa: PLC0415
        except ImportError:
            return []

        client = self._get_client()
        
        try:
            results, _ = client.scroll(
                collection_name=self._cfg.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(key="source_path", match=MatchValue(value=source_path)),
                    ]
                ),
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            return [p.payload for p in results if p.payload]
        except Exception as e:
            logger.error("Failed to fetch chunks from Qdrant: %s", e)
            return []

# ---------------------------------------------------------------------------
# Indexer facade
# ---------------------------------------------------------------------------

class Indexer:
    """
    Facade that keeps ``QdrantIndexer`` in sync (legacy BM25 support removed).
    """

    def __init__(self) -> None:
        self._qdrant = QdrantIndexer()

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def index_chunks(self, chunks: List[Chunk], user_id: str) -> int:
        """
        Upsert *chunks* into Qdrant.

        Returns the number of chunks successfully indexed in Qdrant.
        """
        if not chunks:
            return 0

        try:
            count = self._qdrant.upsert_chunks(chunks)
        except Exception as exc:
            raise IndexingError(f"Qdrant upsert failed: {exc}") from exc

        return count

    def remove_document(self, document_id: str, user_id: str) -> None:
        """Remove all chunks for *document_id* from the index."""
        try:
            self._qdrant.delete_by_document_id(document_id)
        except Exception as exc:
            raise IndexingError(
                f"Qdrant delete for document {document_id} failed: {exc}"
            ) from exc

    def remove_by_source(self, source_path: str, user_id: str) -> None:
        """Remove all chunks for *source_path* from the index."""
        try:
            self._qdrant.delete_by_source_path(source_path)
        except Exception as exc:
            raise IndexingError(
                f"Qdrant delete for source_path {source_path} failed: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _chunk_id_to_int(chunk_id: str) -> int:
    """Convert a UUID string to a stable integer for Qdrant point IDs."""
    import uuid  # noqa: PLC0415
    try:
        return uuid.UUID(chunk_id).int
    except ValueError:
        # Fallback: use hash
        return abs(hash(chunk_id)) % (2 ** 63)


__all__ = [
    "Indexer",
    "QdrantIndexer",
    "IndexingError",
]
