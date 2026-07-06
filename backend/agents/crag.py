"""
agents/crag.py

Corrective RAG (CRAG) agent.

Implements the grade → correct loop:
  1. Grade retrieved chunks via ``DocumentGrader``.
  2. If grades are above threshold → return as-is.
  3. If grades are below threshold → fetch supplementary context from
     web (``RealtimeSearchService``) or code (``CodeSearchTool``) based on settings.
  4. Repeat up to ``CragSettings.max_correction_retries`` times.

Web/code search results are converted to synthetic ``RetrievedChunk`` objects
so the rest of the pipeline can treat them uniformly.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Tuple

from services.document_grader import DocumentGrader
from services.realtime_search import RealtimeSearchService
from tools.code_search import CodeSearchTool
from app.models import RelevanceGrade, RetrievedChunk, RetrievalSource
from app.config import CragSettings, get_settings

logger = logging.getLogger(__name__)


class CragAgent:
    """
    Corrective RAG agent that iteratively improves the chunk set.

    Parameters
    ----------
    grader:
        Inject a pre-built ``DocumentGrader``.
    web_search:
        Inject a pre-built ``RealtimeSearchService``.
    code_search:
        Inject a pre-built ``CodeSearchTool``.
    settings:
        Override ``CragSettings`` (mainly for testing).
    """

    def __init__(
        self,
        grader: Optional[DocumentGrader] = None,
        web_search = None,
        code_search: Optional[CodeSearchTool] = None,
        settings: Optional[CragSettings] = None,
    ) -> None:
        cfg = get_settings()
        self._cfg: CragSettings = settings or cfg.crag
        self._grader = grader or DocumentGrader()
        self._web_search = web_search
        self._code_search = code_search or CodeSearchTool()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def correct(
        self,
        query: str,
        chunks: List[RetrievedChunk],
        force_web_search: bool = False,
    ) -> List[RetrievedChunk]:
        """
        Grade *chunks* and, if necessary, augment with external results.

        Returns the final (potentially corrected) chunk list.
        """
        if not self._cfg.enabled:
            logger.debug("CRAG disabled; returning chunks unchanged.")
            return chunks

        current_chunks = list(chunks)

        for attempt in range(self._cfg.max_correction_retries + 1):
            grades = self._grader.grade(query, current_chunks)
            all_good, needs_correction = self._assess_grades(grades)

            if all_good and not force_web_search:
                logger.info("CRAG: all chunks graded GOOD on attempt %d.", attempt + 1)
                return current_chunks

            if (not needs_correction and not force_web_search) or attempt >= self._cfg.max_correction_retries:
                # Return whatever we have — don't discard partial results
                good_chunks = [c for c, g, _ in grades if g == RelevanceGrade.GOOD]
                return good_chunks if good_chunks else current_chunks

            logger.info(
                "CRAG: correction attempt %d/%d — fetching supplementary context.",
                attempt + 1,
                self._cfg.max_correction_retries,
            )

            extra_chunks = self._fetch_extra_context(query, grades, force_web_search)
            if not extra_chunks:
                logger.warning("CRAG: no extra context retrieved; stopping correction.")
                break

            # Merge: keep GOOD chunks, replace BAD with external results
            good_chunks = [c for c, g, _ in grades if g == RelevanceGrade.GOOD]
            current_chunks = good_chunks + extra_chunks

        return current_chunks

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _assess_grades(
        self, grades: List[Tuple[RetrievedChunk, RelevanceGrade, float]]
    ) -> Tuple[bool, bool]:
        """
        Returns (all_good, needs_correction).

        all_good        — every chunk ≥ relevance_threshold_good
        needs_correction — any chunk < relevance_threshold_bad
        """
        if not grades:
            return False, False

        scores = [score for _, _, score in grades]
        all_good = all(s >= self._cfg.relevance_threshold_good for s in scores)
        needs_correction = any(s < self._cfg.relevance_threshold_bad for s in scores)
        return all_good, needs_correction

    def _fetch_extra_context(
        self,
        query: str,
        grades: List[Tuple[RetrievedChunk, RelevanceGrade, float]],
        force_web_search: bool = False,
    ) -> List[RetrievedChunk]:
        """Fetch supplementary context from enabled fallback sources."""
        extra: List[RetrievedChunk] = []

        # Web search fallback
        if self._cfg.web_search_fallback or force_web_search:
            try:
                if self._web_search is None:
                    from services.realtime_search import RealtimeSearchService
                    self._web_search = RealtimeSearchService()
                extra.extend(self._web_search.search(query))
            except Exception as exc:  # noqa: BLE001
                logger.warning("CRAG web search unexpected error: %s", exc)

        # Code search fallback
        if self._cfg.code_search_fallback and not extra:
            try:
                import os  # noqa: PLC0415
                repo_path = os.getcwd()
                code_results = self._code_search.search(query, repo_path=repo_path, top_k=3)
                for result in code_results:
                    snippet = result.get("snippet", "").strip()
                    if snippet:
                        extra.append(
                            RetrievedChunk(
                                chunk_id=f"code:{hash(snippet) & 0xFFFFFFFF:08x}",
                                document_id=result.get("file_path", "code"),
                                text=snippet,
                                source=RetrievalSource.CODE,
                                metadata={
                                    "file_path": result.get("file_path", ""),
                                    "symbol_name": result.get("symbol_name", ""),
                                    "line_number": result.get("line_number", 0),
                                    "source_type": "code",
                                },
                            )
                        )
            except Exception as exc:  # noqa: BLE001
                logger.warning("CRAG code search fallback failed: %s", exc)

        return extra


__all__ = ["CragAgent"]
