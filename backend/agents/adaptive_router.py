"""
agents/adaptive_router.py

Pure decision function — no I/O, no external dependencies.

Maps a ``QueryIntent`` (and optional CRAG grading results) to one of five
routing targets:
  "local_rag"  — answer from the local vector+BM25 index
  "web"        — answer requires live web search
  "hybrid"     — combine local RAG with web search results
  "tool"       — use a specialised tool (code search, calculator, etc.)
  "agent"      — hand off to a multi-step agent loop
"""

from __future__ import annotations

import logging
from typing import List, Optional, Tuple

from app.models import QueryIntent, RelevanceGrade

logger = logging.getLogger(__name__)

# Typing alias for the CRAG grading triples passed from DocumentGrader
GradingResults = List[Tuple[object, RelevanceGrade, float]]


class AdaptiveRouter:
    """
    Decides the retrieval/generation strategy for a given intent and
    optional CRAG grading results.

    This class contains no I/O — it is a pure decision function that
    ``services/rag_pipeline.py`` calls to select the next pipeline branch.
    """

    def decide_route(
        self,
        intent: QueryIntent,
        grades: Optional[GradingResults] = None,
    ) -> str:
        """
        Return the routing target string.

        Parameters
        ----------
        intent:
            The ``QueryIntent`` produced by ``QueryRouter``.
        grades:
            Optional list of ``(chunk, grade, score)`` triples from
            ``DocumentGrader``.  When provided, the grade distribution
            influences the routing decision.

        Returns
        -------
        One of: ``"local_rag"``, ``"web"``, ``"hybrid"``, ``"tool"``,
        ``"agent"``.
        """
        # First pass: intent-only routing
        route = self._intent_route(intent)

        # Second pass: refine based on CRAG grades when available
        if grades is not None:
            route = self._refine_with_grades(route, grades)

        logger.info("AdaptiveRouter: intent=%s → route=%s", intent.value, route)
        return route

    # ------------------------------------------------------------------
    # Intent-based routing
    # ------------------------------------------------------------------

    @staticmethod
    def _intent_route(intent: QueryIntent) -> str:
        mapping = {
            QueryIntent.SIMPLE_QA: "local_rag",
            QueryIntent.COMPLEX_QA: "local_rag",
            QueryIntent.CODE_SEARCH: "tool",
            QueryIntent.WEB_SEARCH: "web",
            QueryIntent.HYBRID_SEARCH: "hybrid",
        }
        return mapping.get(intent, "local_rag")

    # ------------------------------------------------------------------
    # Grade-based refinement
    # ------------------------------------------------------------------

    @staticmethod
    def _refine_with_grades(current_route: str, grades: GradingResults) -> str:
        """
        Upgrade the route if grading indicates local results are insufficient.

        Logic:
          - If all chunks are BAD → upgrade to "web" (or keep if already "web").
          - If majority are NEED_WEB → upgrade to "hybrid".
          - Otherwise keep the intent-based route.
        """
        if not grades:
            return current_route

        total = len(grades)
        bad_count = sum(1 for _, g, _ in grades if g == RelevanceGrade.BAD)
        need_web_count = sum(1 for _, g, _ in grades if g == RelevanceGrade.NEED_WEB)

        if bad_count == total:
            # No relevant local results → web only
            return "web"

        if need_web_count > total / 2:
            # Most chunks need supplementing with web data
            if current_route == "local_rag":
                return "hybrid"

        return current_route


__all__ = ["AdaptiveRouter"]
