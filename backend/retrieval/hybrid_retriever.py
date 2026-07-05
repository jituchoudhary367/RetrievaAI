"""
retrieval/hybrid_retriever.py

Hybrid retriever combining dense (Qdrant) and sparse (BM42/SPLADE) search via
Qdrant Native Hybrid Search and Reciprocal Rank Fusion (RRF).

Pipeline:
  1. Embed query → dense vector and sparse vector via Embedder.embed_query_dual(query)
  2. Construct Qdrant Prefetch query (text-dense + text-sparse) with RRF Fusion
  3. Deduplicate and merge adjacent chunks (safe token length)
  4. Truncate to top_k_final
"""

from __future__ import annotations

import logging
import time
from typing import Dict, List, Optional, Tuple

from pipeline.indexer import QdrantIndexer
from pipeline.embedder import Embedder
from retrieval.filters import build_qdrant_filter
from app.config import RetrievalSettings, get_settings
from app.models import RetrievedChunk, MetadataFilter, RetrievalSource

logger = logging.getLogger(__name__)


class HybridRetriever:
    """
    Retrieves chunks via Qdrant Native Hybrid Search.

    Parameters
    ----------
    embedder:
        An ``Embedder`` instance used to embed the query.
    qdrant_indexer:
        A ``QdrantIndexer`` for dense search.
    settings:
        Override ``RetrievalSettings`` (mainly for testing).
    """

    def __init__(
        self,
        embedder: Optional[Embedder] = None,
        qdrant_indexer: Optional[QdrantIndexer] = None,
        settings: Optional[RetrievalSettings] = None,
    ) -> None:
        cfg = get_settings()
        self._cfg: RetrievalSettings = settings or cfg.retrieval
        self._embedder = embedder or Embedder()
        self._qdrant = qdrant_indexer or QdrantIndexer()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def retrieve(
        self,
        query: str,
        user_id: str,
        top_k: Optional[int] = None,
        filters: Optional[List[MetadataFilter]] = None,
        retrieval_mode: str = "hybrid",
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
        retrieval_mode:
            "hybrid", "vector", or "keyword"

        Returns
        -------
        List of ``RetrievedChunk`` sorted by descending fused score.
        """
        t0 = time.time()
        
        # Adaptive Retrieval Heuristic
        # Simple < 5 words, Medium 5-10 words, Complex > 10 words
        word_count = len(query.split())
        if top_k is None:
            if word_count < 5:
                final_k = 5
            elif word_count <= 10:
                final_k = 8
            else:
                final_k = 12
        else:
            final_k = top_k

        # 1. Embed query
        query_dense = None
        query_sparse = None
        
        t1 = time.time()
        try:
            query_dense, query_sparse = self._embedder.embed_query_dual(query)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to embed query: %s", exc)
        t2 = time.time()
        logger.info("Embedding latency: %.3fs", t2 - t1)

        # 2. Qdrant Native Hybrid Search
        user_filter = MetadataFilter(field="user_id", value=user_id, operator="eq")
        merged_filters = [user_filter]
        if filters:
            merged_filters.extend(filters)
        qdrant_filter = build_qdrant_filter(merged_filters)
        
        try:
            from qdrant_client.http import models  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError("qdrant-client is required") from exc

        prefetch_list = []
        if retrieval_mode in ("hybrid", "vector") and query_dense is not None:
            prefetch_list.append(
                models.Prefetch(
                    query=query_dense,
                    using="text-dense",
                    limit=self._cfg.top_k_dense,
                    filter=qdrant_filter
                )
            )
            
        if retrieval_mode in ("hybrid", "keyword") and query_sparse is not None:
            indices = query_sparse.indices.tolist() if hasattr(query_sparse.indices, "tolist") else list(query_sparse.indices)
            values = query_sparse.values.tolist() if hasattr(query_sparse.values, "tolist") else list(query_sparse.values)
            prefetch_list.append(
                models.Prefetch(
                    query=models.SparseVector(indices=indices, values=values),
                    using="text-sparse",
                    limit=self._cfg.top_k_sparse,
                    filter=qdrant_filter
                )
            )

        scored_points = []
        t3 = time.time()
        if prefetch_list:
            try:
                client = self._qdrant._get_client()
                scored_points = client.query_points(
                    collection_name=self._qdrant._cfg.collection_name,
                    prefetch=prefetch_list,
                    query=models.FusionQuery(fusion=models.Fusion.RRF),
                    limit=self._cfg.top_k_dense + self._cfg.top_k_sparse, # Fetch more to allow merging
                ).points
            except Exception as exc:  # noqa: BLE001
                logger.warning("Qdrant Native Hybrid search failed: %s", exc)
        t4 = time.time()
        logger.info("Qdrant search latency: %.3fs", t4 - t3)

        # 3. Deduplicate and Merge
        results = self._process_and_merge_chunks(scored_points)
        
        # 4. Truncate
        results = results[:final_k]

        logger.info(
            "HybridRetriever: retrieved %d fused chunks (final_k=%d). Total latency: %.3fs",
            len(results),
            final_k,
            time.time() - t0
        )
        return results

    def _process_and_merge_chunks(self, scored_points: list) -> List[RetrievedChunk]:
        """
        Deduplicates chunks and merges adjacent chunks from the same document.
        """
        if not scored_points:
            return []

        # Deduplicate
        seen = set()
        unique_points = []
        for p in scored_points:
            cid = p.payload.get("chunk_id", str(p.id))
            if cid not in seen:
                seen.add(cid)
                unique_points.append(p)
                
        # Create initial RetrievedChunk objects
        chunks = []
        for p in unique_points:
            cid = p.payload.get("chunk_id", str(p.id))
            payload = p.payload
            chunks.append(
                RetrievedChunk(
                    chunk_id=cid,
                    document_id=payload.get("document_id", ""),
                    text=payload.get("text", ""),
                    source=RetrievalSource.VECTOR,  # Native hybrid abstracts this
                    dense_score=None,
                    sparse_score=None,
                    fused_score=float(p.score),
                    metadata={k: v for k, v in payload.items() if k not in {"chunk_id", "document_id", "text"}},
                )
            )

        # Merge adjacent chunks safely
        merged_results = []
        skip = set()
        
        for i, current in enumerate(chunks):
            if current.chunk_id in skip:
                continue
            
            merged_chunk = current
            
            # Look ahead for adjacent chunks in the current result set
            for j in range(i + 1, len(chunks)):
                nxt = chunks[j]
                if nxt.chunk_id in skip:
                    continue
                
                # Check adjacency
                if current.document_id == nxt.document_id:
                    idx1 = current.metadata.get("chunk_index", -1)
                    idx2 = nxt.metadata.get("chunk_index", -1)
                    
                    if idx1 != -1 and idx2 != -1 and abs(idx1 - idx2) == 1:
                        # Adjacent! Let's merge if text length is safe (< 5000 chars roughly)
                        if len(current.text) + len(nxt.text) < 5000:
                            if idx1 < idx2:
                                merged_text = current.text + "\n\n" + nxt.text
                            else:
                                merged_text = nxt.text + "\n\n" + current.text
                                
                            merged_chunk.text = merged_text
                            skip.add(nxt.chunk_id)
            
            merged_results.append(merged_chunk)

        return merged_results

__all__ = ["HybridRetriever"]
