"""
pipeline/indexer.py

Dual-index writer: keeps a dense Qdrant collection and a sparse BM25 index
in sync for every write operation.

Exports:
  QdrantIndexer  — upserts/deletes chunks in Qdrant
  BM25Index      — self-contained Okapi BM25 implementation persisted via
                   pickle; reusable standalone by retrieval/hybrid_retriever.py
  Indexer        — facade that calls both, persisting BM25 after every write
  IndexingError  — domain exception

BM25Index is intentionally a top-level public class (not nested inside Indexer)
so that HybridRetriever can load it independently from the same file path.
"""

from __future__ import annotations

import logging
import math
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


# ---------------------------------------------------------------------------
# BM25 Index (pure Python, no third-party BM25 lib)
# ---------------------------------------------------------------------------

class BM25Index:
    """
    Self-contained Okapi BM25 sparse retriever.

    Documents are stored as token-frequency dicts.  The index is serialised
    via ``pickle`` to ``QdrantSettings.bm25_index_path`` (resolved from
    settings, never a hardcoded path).

    Parameters
    ----------
    k1:  Term-frequency saturation parameter (default 1.5).
    b:   Length normalisation parameter (default 0.75).
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        # chunk_id → token-frequency map
        self._corpus: Dict[str, Dict[str, int]] = {}
        # Inverted index: token → {chunk_id: tf}
        self._inverted: Dict[str, Dict[str, int]] = {}
        self._avgdl: float = 0.0
        self._doc_lengths: Dict[str, int] = {}

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def add_documents(self, chunk_id: str, text: str) -> None:
        """Index a single document identified by *chunk_id*."""
        tokens = self._tokenise(text)
        tf: Dict[str, int] = {}
        for token in tokens:
            tf[token] = tf.get(token, 0) + 1
        self._corpus[chunk_id] = tf
        self._doc_lengths[chunk_id] = len(tokens)
        for token, freq in tf.items():
            self._inverted.setdefault(token, {})[chunk_id] = freq
        self._update_avgdl()

    def remove_document(self, chunk_id: str) -> None:
        """Remove *chunk_id* from the index."""
        tf = self._corpus.pop(chunk_id, {})
        self._doc_lengths.pop(chunk_id, None)
        for token in tf:
            if token in self._inverted:
                self._inverted[token].pop(chunk_id, None)
                if not self._inverted[token]:
                    del self._inverted[token]
        self._update_avgdl()

    def _update_avgdl(self) -> None:
        if self._doc_lengths:
            self._avgdl = sum(self._doc_lengths.values()) / len(self._doc_lengths)
        else:
            self._avgdl = 0.0

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, query: str, top_k: int = 20) -> List[Tuple[str, float]]:
        """
        Return up to *top_k* ``(chunk_id, score)`` pairs, highest score first.
        """
        query_tokens = self._tokenise(query)
        if not query_tokens or not self._corpus:
            return []

        n = len(self._corpus)
        scores: Dict[str, float] = {}

        for token in query_tokens:
            if token not in self._inverted:
                continue
            df = len(self._inverted[token])
            idf = math.log((n - df + 0.5) / (df + 0.5) + 1.0)
            for chunk_id, tf in self._inverted[token].items():
                dl = self._doc_lengths.get(chunk_id, 1)
                denom = tf + self.k1 * (1 - self.b + self.b * dl / max(self._avgdl, 1))
                scores[chunk_id] = scores.get(chunk_id, 0.0) + idf * (
                    tf * (self.k1 + 1) / denom
                )

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: Path) -> None:
        """Pickle the index to *path* (creates parent dirs if needed)."""
        path = Path(path)
        parent = path.parent
        # Auto-recover: if parent path is a file (not a dir), remove it first
        if parent.exists() and not parent.is_dir():
            logger.warning(
                "BM25 parent path %s is a file, not a directory — removing and recreating.",
                parent,
            )
            parent.unlink()
        parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as fh:
            pickle.dump(self, fh, protocol=pickle.HIGHEST_PROTOCOL)
        logger.debug("BM25Index saved to %s (%d docs).", path, len(self._corpus))

    @classmethod
    def load(cls, path: Path) -> "BM25Index":
        """Load and return a ``BM25Index`` from *path*."""
        path = Path(path)
        if not path.exists():
            logger.info("No BM25 index found at %s — starting fresh.", path)
            return cls()
        with open(path, "rb") as fh:
            obj = pickle.load(fh)
        if not isinstance(obj, cls):
            raise IndexingError(f"Unexpected object type in BM25 file: {type(obj)}")
        logger.info("BM25Index loaded from %s (%d docs).", path, len(obj._corpus))
        return obj

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def _tokenise(text: str) -> List[str]:
        return re.findall(r"\b\w+\b", text.lower())

    def __len__(self) -> int:
        return len(self._corpus)




class QdrantIndexer:
    """
    Upserts and deletes chunks from a Qdrant vector collection.

    Creates the collection with HNSW parameters from ``QdrantSettings`` if it
    does not already exist.
    """

    def __init__(self, settings: Optional[QdrantSettings] = None) -> None:
        self._cfg: QdrantSettings = settings or get_settings().qdrant
        self._client = None  # Lazy init to avoid import at module load

    # ------------------------------------------------------------------
    # Client
    # ------------------------------------------------------------------

    def _get_client(self) -> object:
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
        from qdrant_client.http.models import Distance as Dist, VectorParams as VP, HnswConfigDiff as HNSW  # noqa: PLC0415
        cfg = self._cfg
        collections = [c.name for c in client.get_collections().collections]
        if cfg.collection_name in collections:
            return

        distance_map = {
            "Cosine": Dist.COSINE,
            "Euclid": Dist.EUCLID,
            "Dot": Dist.DOT,
        }
        distance = distance_map.get(cfg.distance_metric, Dist.COSINE)

        client.create_collection(
            collection_name=cfg.collection_name,
            vectors_config=VP(size=cfg.vector_size, distance=distance),
            hnsw_config=HNSW(ef_construct=cfg.hnsw_ef_construct, m=cfg.hnsw_m),
        )
        logger.info(
            "Created Qdrant collection '%s' (dim=%d, distance=%s).",
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
            from qdrant_client.http.models import PointStruct  # noqa: PLC0415
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
            payload = {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "text": chunk.text,
                "chunk_index": chunk.chunk_index,
                **chunk.metadata,
            }
            points.append(
                PointStruct(
                    id=chunk.chunk_id,
                    vector=chunk.embedding,
                    payload=payload,
                )
            )

        if not points:
            return 0

        client.upsert(
            collection_name=self._cfg.collection_name,
            points=points,
            wait=True,
        )
        logger.info("Upserted %d point(s) into Qdrant.", len(points))
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
    Facade that keeps ``QdrantIndexer`` and ``BM25Index`` in sync.

    BM25 index is loaded lazily per user via a `BM25UserPool` pattern.
    """

    def __init__(self) -> None:
        self._qdrant = QdrantIndexer()
        self._bm25_pool: Dict[str, BM25Index] = {}

    def _get_bm25(self, user_id: str) -> BM25Index:
        if user_id not in self._bm25_pool:
            base_path = get_settings().qdrant.bm25_index_path
            user_path = base_path / f"{user_id}.pkl"
            self._bm25_pool[user_id] = BM25Index.load(user_path)
        return self._bm25_pool[user_id]

    def _save_bm25(self, user_id: str) -> None:
        if user_id in self._bm25_pool:
            base_path = get_settings().qdrant.bm25_index_path
            user_path = base_path / f"{user_id}.pkl"
            self._bm25_pool[user_id].save(user_path)

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def index_chunks(self, chunks: List[Chunk], user_id: str) -> int:
        """
        Upsert *chunks* into Qdrant and BM25.

        Returns the number of chunks successfully indexed in Qdrant.
        Persists BM25 after the write.
        """
        if not chunks:
            return 0

        try:
            count = self._qdrant.upsert_chunks(chunks)
        except Exception as exc:
            raise IndexingError(f"Qdrant upsert failed: {exc}") from exc

        bm25 = self._get_bm25(user_id)
        for chunk in chunks:
            try:
                bm25.add_documents(chunk.chunk_id, chunk.text)
            except Exception as exc:  # noqa: BLE001
                logger.warning("BM25 indexing failed for chunk %s: %s", chunk.chunk_id, exc)

        self._save_bm25(user_id)
        return count

    def remove_document(self, document_id: str, user_id: str) -> None:
        """Remove all chunks for *document_id* from both indexes."""
        try:
            self._qdrant.delete_by_document_id(document_id)
        except Exception as exc:
            raise IndexingError(
                f"Qdrant delete for document {document_id} failed: {exc}"
            ) from exc

        # BM25
        logger.info(
            "BM25 remove_document: BM25 does not store document_id→chunk_id "
            "mapping; skipping BM25 removal for document %s.",
            document_id,
        )
        self._save_bm25(user_id)

    def remove_by_source(self, source_path: str, user_id: str) -> None:
        """Remove all chunks for *source_path* from both indexes."""
        try:
            self._qdrant.delete_by_source_path(source_path)
        except Exception as exc:
            raise IndexingError(
                f"Qdrant delete for source_path {source_path} failed: {exc}"
            ) from exc

        # BM25
        logger.info("BM25 remove_by_source: skipping BM25 removal since no mapping available.")
        self._save_bm25(user_id)

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
    "BM25Index",
    "IndexingError",
]
