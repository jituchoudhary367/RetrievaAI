"""
retrieval/reranker.py

Cross-encoder reranker applied after hybrid retrieval.

Gated by ``RetrievalSettings.rerank_enabled``:
  - When enabled and ``sentence-transformers`` is installed, runs the
    configured cross-encoder model to produce a relevance score for each
    (query, chunk) pair.
  - When disabled *or* the library is missing, returns the input list
    unchanged (no-op with a debug log).

Each returned ``RetrievedChunk`` has ``.rerank_score`` set.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from app.config import RetrievalSettings, get_settings
from app.models import RetrievedChunk

logger = logging.getLogger(__name__)


class Reranker:
    """
    Cross-encoder reranker using ``sentence-transformers`` ``CrossEncoder``.

    Parameters
    ----------
    settings:
        Override ``RetrievalSettings`` (mainly for testing).
    """

    def __init__(self, settings: Optional[RetrievalSettings] = None) -> None:
        self._cfg: RetrievalSettings = settings or get_settings().retrieval
        self._model = None  # lazy init

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def rerank(
        self,
        query: str,
        chunks: List[RetrievedChunk],
        top_n: Optional[int] = None,
    ) -> List[RetrievedChunk]:
        """
        Rerank *chunks* by relevance to *query*.

        Parameters
        ----------
        query:
            The user's query string.
        chunks:
            Candidates from the hybrid retriever.
        top_n:
            Override the configured ``rerank_top_n`` count.  If ``None``,
            uses ``RetrievalSettings.rerank_top_n``.

        Returns
        -------
        Reranked (and truncated) list with ``.rerank_score`` populated.
        If reranking is disabled or the library is unavailable, returns
        *chunks* unchanged.
        """
        if not chunks:
            return chunks

        n = top_n if top_n is not None else self._cfg.rerank_top_n

        if not self._cfg.rerank_enabled:
            logger.debug("Reranking disabled; returning input unchanged.")
            return chunks[:n]

        model = self._load_model()
        if model is None:
            logger.warning(
                "Cross-encoder model could not be loaded; skipping rerank."
            )
            return chunks[:n]

        pairs = [(query, chunk.text) for chunk in chunks]
        try:
            scores = model.predict(pairs)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Cross-encoder predict failed: %s — returning unreranked.", exc)
            return chunks[:n]

        for chunk, score in zip(chunks, scores):
            chunk.rerank_score = float(score)

        reranked = sorted(chunks, key=lambda c: c.rerank_score or 0.0, reverse=True)
        logger.info("Reranked %d → %d chunks.", len(reranked), min(n, len(reranked)))
        return reranked[:n]

    # ------------------------------------------------------------------
    # Lazy model loading
    # ------------------------------------------------------------------

    def _load_model(self) -> Optional[object]:
        if self._model is not None:
            return self._model
        try:
            from sentence_transformers import CrossEncoder  # noqa: PLC0415
            self._model = CrossEncoder(
                self._cfg.rerank_model,
                max_length=512,
            )
            logger.info("CrossEncoder loaded: %s", self._cfg.rerank_model)
            return self._model
        except ImportError:
            logger.warning(
                "sentence-transformers not installed — reranking unavailable. "
                "Install with: pip install sentence-transformers"
            )
            return None
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load CrossEncoder model: %s", exc)
            return None


__all__ = ["Reranker"]
