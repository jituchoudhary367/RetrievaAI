"""
retrieval/hybrid_retriever.py

Hybrid retriever combining dense (Qdrant) and sparse (BM25) search via
Reciprocal Rank Fusion (RRF).

Pipeline:
  1. Embed query → dense vector via Embedder.embed_texts([query])[0]
  2. Dense search → top_k_dense hits from QdrantIndexer
  3. Sparse search → top_k_sparse hits from BM25Index
  4. Fuse ranked lists with RRF using rrf_k and hybrid_alpha weighting
  5. Truncate to top_k_final (or caller-supplied top_k)

BM25Index and bm25_index_path are resolved from settings — the same path
used by pipeline/indexer.py so both read/write the same persisted file.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

from pipeline.indexer import QdrantIndexer, BM25Index
from pipeline.embedder import Embedder
from retrieval.filters import build_qdrant_filter
from app.config import RetrievalSettings, get_settings
from app.models import RetrievedChunk, MetadataFilter, RetrievalSource

logger = logging.getLogger(__name__)


class HybridRetriever:
    """
    Retrieves chunks via dense + sparse search fused with RRF.

    Parameters
    ----------
    embedder:
        An ``Embedder`` instance used to embed the query.
    qdrant_indexer:
        A ``QdrantIndexer`` for dense search.
    bm25_index:
        A ``BM25Index`` for sparse search.  When ``None``, loaded from
        ``get_settings().qdrant.bm25_index_path``.
    settings:
        Override ``RetrievalSettings`` (mainly for testing).
    """

    def __init__(
        self,
        embedder: Optional[Embedder] = None,
        qdrant_indexer: Optional[QdrantIndexer] = None,
        bm25_index: Optional[BM25Index] = None,
        settings: Optional[RetrievalSettings] = None,
    ) -> None:
        cfg = get_settings()
        self._cfg: RetrievalSettings = settings or cfg.retrieval
        self._embedder = embedder or Embedder()
        self._qdrant = qdrant_indexer or QdrantIndexer()
        if bm25_index is not None:
            self._bm25 = bm25_index
        else:
            self._bm25 = BM25Index.load(cfg.qdrant.bm25_index_path)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[List[MetadataFilter]] = None,
    ) -> List[RetrievedChunk]:
        """
        Retrieve relevant chunks for *query*.

        Parameters
        ----------
        query:
            The user's search string.
        top_k:
            Override the configured ``top_k_final`` count.
        filters:
            Optional metadata filters applied to the dense leg only.

        Returns
        -------
        List of ``RetrievedChunk`` sorted by descending fused score.
        """
        final_k = top_k if top_k is not None else self._cfg.top_k_final

        # 1. Embed query
        try:
            query_vector = self._embedder.embed_texts([query])[0]
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to embed query: %s", exc)
            return []

        # 2. Dense search
        qdrant_filter = build_qdrant_filter(filters or [])
        dense_hits: List[Tuple[str, float]] = []
        try:
            scored_points = self._qdrant.search(
                query_vector=query_vector,
                top_k=self._cfg.top_k_dense,
                query_filter=qdrant_filter,
            )
            for point in scored_points:
                chunk_id = point.payload.get("chunk_id", str(point.id))
                dense_hits.append((chunk_id, float(point.score)))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Qdrant dense search failed: %s", exc)

        # 3. Sparse search (BM25)
        sparse_hits: List[Tuple[str, float]] = []
        try:
            sparse_hits = self._bm25.search(query, top_k=self._cfg.top_k_sparse)
        except Exception as exc:  # noqa: BLE001
            logger.warning("BM25 sparse search failed: %s", exc)

        # 4. Reciprocal Rank Fusion
        fused = self._rrf(dense_hits, sparse_hits)

        # 5. Truncate and build result objects
        fused = fused[:final_k]
        chunk_ids = {cid for cid, _ in fused}
        dense_score_map: Dict[str, float] = dict(dense_hits)
        sparse_score_map: Dict[str, float] = dict(sparse_hits)

        # Collect payloads from Qdrant for the fused set
        payloads = self._fetch_payloads(chunk_ids, scored_points if dense_hits else [])

        results: List[RetrievedChunk] = []
        for chunk_id, fused_score in fused:
            payload = payloads.get(chunk_id, {})
            results.append(
                RetrievedChunk(
                    chunk_id=chunk_id,
                    document_id=payload.get("document_id", ""),
                    text=payload.get("text", ""),
                    source=RetrievalSource.VECTOR
                    if chunk_id in dense_score_map
                    else RetrievalSource.BM25,
                    dense_score=dense_score_map.get(chunk_id),
                    sparse_score=sparse_score_map.get(chunk_id),
                    fused_score=fused_score,
                    metadata={k: v for k, v in payload.items()
                               if k not in {"chunk_id", "document_id", "text"}},
                )
            )

        logger.info(
            "HybridRetriever: %d dense, %d sparse → %d fused results.",
            len(dense_hits),
            len(sparse_hits),
            len(results),
        )
        return results

    # ------------------------------------------------------------------
    # RRF
    # ------------------------------------------------------------------

    def _rrf(
        self,
        dense_hits: List[Tuple[str, float]],
        sparse_hits: List[Tuple[str, float]],
    ) -> List[Tuple[str, float]]:
        """
        Reciprocal Rank Fusion with ``hybrid_alpha`` weighting.

        RRF score = alpha * 1/(k+rank_dense) + (1-alpha) * 1/(k+rank_sparse)
        """
        k = self._cfg.rrf_k
        alpha = self._cfg.hybrid_alpha

        scores: Dict[str, float] = {}

        for rank, (chunk_id, _) in enumerate(dense_hits, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + alpha / (k + rank)

        for rank, (chunk_id, _) in enumerate(sparse_hits, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + (1 - alpha) / (k + rank)

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked

    # ------------------------------------------------------------------
    # Payload helper
    # ------------------------------------------------------------------

    @staticmethod
    def _fetch_payloads(
        chunk_ids: set,
        scored_points: list,
    ) -> Dict[str, dict]:
        """Build a chunk_id → payload dict from Qdrant scored points."""
        payloads: Dict[str, dict] = {}
        for point in scored_points:
            cid = point.payload.get("chunk_id", str(point.id))
            if cid in chunk_ids:
                payloads[cid] = dict(point.payload)
        return payloads


__all__ = ["HybridRetriever"]
