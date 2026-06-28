"""
tools/vector_search.py

Thin pass-through wrapper over ``HybridRetriever`` that exposes a simple
``search()`` interface for use by agents and services.

This indirection keeps ``agents/`` and ``services/`` decoupled from the
retrieval internals — they call ``VectorSearchTool.search()``, not
``HybridRetriever.retrieve()`` directly.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from retrieval.hybrid_retriever import HybridRetriever
from app.models import RetrievedChunk, MetadataFilter

logger = logging.getLogger(__name__)


class VectorSearchTool:
    """
    Thin adapter over ``HybridRetriever`` for use by agents and services.

    Parameters
    ----------
    retriever:
        Inject a pre-built ``HybridRetriever`` (mainly for testing).
        When ``None``, a default instance is created on first use.
    """

    def __init__(self, retriever: Optional[HybridRetriever] = None) -> None:
        self._retriever: Optional[HybridRetriever] = retriever

    @property
    def _get_retriever(self) -> HybridRetriever:
        if self._retriever is None:
            self._retriever = HybridRetriever()
        return self._retriever

    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[List[MetadataFilter]] = None,
    ) -> List[RetrievedChunk]:
        """
        Search the vector store for chunks relevant to *query*.

        Parameters
        ----------
        query:
            The search query.
        top_k:
            Maximum number of results to return.
        filters:
            Optional metadata filters applied during retrieval.

        Returns
        -------
        A list of ``RetrievedChunk`` objects sorted by descending score.
        """
        logger.debug("VectorSearchTool.search: query=%r top_k=%d", query, top_k)
        return self._get_retriever.retrieve(query=query, top_k=top_k, filters=filters)


__all__ = ["VectorSearchTool"]
