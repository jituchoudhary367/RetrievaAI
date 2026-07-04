"""
services/document_grader.py

Grades retrieved chunks for relevance using the CRAG grading prompt.

For each ``RetrievedChunk``, calls the configured LLM with the relevance
grading prompt from ``prompts/grading.py`` and returns a
``(RetrievedChunk, RelevanceGrade, float)`` triple.

The grading step is gated by ``CragSettings.enabled`` — when CRAG is
disabled this service still works but callers (e.g. CragAgent) may not
invoke it.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Tuple

from app.models import RelevanceGrade, RetrievedChunk
from prompts.grading import render_relevance_grading_prompt, parse_grading_response
from app.config import CragSettings, get_settings

logger = logging.getLogger(__name__)


class DocumentGrader:
    """
    Grades retrieved chunks for relevance to a query.

    Parameters
    ----------
    crag_settings:
        Override ``CragSettings`` (mainly for testing).
    """

    def __init__(self, crag_settings: Optional[CragSettings] = None) -> None:
        cfg = get_settings()
        self._cfg: CragSettings = crag_settings or cfg.crag
        self._llm_cfg = cfg.llm

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def grade(
        self,
        query: str,
        chunks: List[RetrievedChunk],
    ) -> List[Tuple[RetrievedChunk, RelevanceGrade, float]]:
        """
        Grade each chunk in *chunks* for relevance to *query*.

        Parameters
        ----------
        query:
            The user's query string.
        chunks:
            Candidate chunks from the retriever.

        Returns
        -------
        List of ``(RetrievedChunk, RelevanceGrade, score)`` triples in the
        same order as *chunks*.  On LLM failure for a specific chunk, the
        grade defaults to ``BAD`` with score 0.0 (conservative).
        """
        results: List[Tuple[RetrievedChunk, RelevanceGrade, float]] = []

        for chunk in chunks:
            grade, score = self._grade_one(query, chunk)
            results.append((chunk, grade, score))

        good_count = sum(1 for _, g, _ in results if g == RelevanceGrade.GOOD)
        logger.info(
            "DocumentGrader: %d/%d chunks graded GOOD for query %r.",
            good_count,
            len(chunks),
            query[:60],
        )
        return results

    # ------------------------------------------------------------------
    # Per-chunk grading
    # ------------------------------------------------------------------

    def _grade_one(
        self, query: str, chunk: RetrievedChunk
    ) -> Tuple[RelevanceGrade, float]:
        prompt = render_relevance_grading_prompt(query, chunk.text)
        try:
            raw = self._call_llm(prompt)
            if raw:
                return parse_grading_response(raw)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Grading failed for chunk %s: %s — defaulting to BAD.",
                chunk.chunk_id,
                exc,
            )
        return RelevanceGrade.BAD, 0.0

    def _call_llm(self, prompt: str) -> Optional[str]:
        cfg = get_settings()
        provider = cfg.llm.provider.value
        api_key = cfg.resolved_llm_api_key()

        if provider == "anthropic":
            import anthropic  # noqa: PLC0415
            client = anthropic.Anthropic(api_key=api_key)
            msg = client.messages.create(
                model=self._llm_cfg.model_name,
                max_tokens=128,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text if msg.content else None

        if provider in ("openai", "groq", "openrouter"):
            import openai  # noqa: PLC0415
            oc = openai.OpenAI(api_key=api_key, base_url=cfg.resolved_llm_base_url())
            resp = oc.chat.completions.create(
                model=self._llm_cfg.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=128,
                temperature=0.0,
            )
            return resp.choices[0].message.content

        logger.warning("DocumentGrader: unsupported LLM provider %s.", provider)
        return None


__all__ = ["DocumentGrader"]
