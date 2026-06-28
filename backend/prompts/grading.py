"""
prompts/grading.py

Relevance grading prompt and response parser for the CRAG document grader.

``render_relevance_grading_prompt`` produces a prompt whose expected LLM
output maps cleanly onto ``RelevanceGrade`` (good / bad / need_web) plus a
0–1 numeric confidence score.

``parse_grading_response`` turns the raw LLM string into
``(RelevanceGrade, float)`` for ``services/document_grader.py``.
"""

from __future__ import annotations

import logging
import re
from typing import Tuple

from app.models import RelevanceGrade

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Grading prompt
# ---------------------------------------------------------------------------

def render_relevance_grading_prompt(query: str, chunk_text: str) -> str:
    """
    Render the relevance grading prompt for a single (query, chunk) pair.

    The model is instructed to output exactly:
        GRADE: good|bad|need_web
        SCORE: <float 0.0–1.0>
        REASON: <one sentence>

    GRADE meanings:
      good      — the chunk is directly relevant and sufficient.
      bad       — the chunk is irrelevant or misleading.
      need_web  — the chunk is partially relevant but current web data is
                  required to complete the answer.
    """
    return (
        "You are a relevance grading assistant. Your task is to assess "
        "whether the provided document chunk is relevant to the user's query.\n\n"
        f"Query: {query}\n\n"
        f"Document chunk:\n{chunk_text}\n\n"
        "Grade the relevance using EXACTLY this format (no extra text):\n"
        "GRADE: good|bad|need_web\n"
        "SCORE: <float between 0.0 and 1.0>\n"
        "REASON: <one sentence explaining your grade>\n\n"
        "Grading criteria:\n"
        "  good     — chunk directly answers or strongly supports the query\n"
        "  bad      — chunk is off-topic, irrelevant, or actively misleading\n"
        "  need_web — chunk is relevant but requires up-to-date web information\n\n"
        "Grade:"
    )


# ---------------------------------------------------------------------------
# Response parser
# ---------------------------------------------------------------------------

_GRADE_RE = re.compile(r"GRADE:\s*(good|bad|need_web)", re.IGNORECASE)
_SCORE_RE = re.compile(r"SCORE:\s*([0-9]*\.?[0-9]+)", re.IGNORECASE)

_GRADE_MAP = {
    "good": RelevanceGrade.GOOD,
    "bad": RelevanceGrade.BAD,
    "need_web": RelevanceGrade.NEED_WEB,
}


def parse_grading_response(raw: str) -> Tuple[RelevanceGrade, float]:
    """
    Parse the LLM's grading response into ``(RelevanceGrade, score)``.

    Tolerant parser: falls back to ``BAD`` / 0.0 when the model output
    doesn't match the expected format, logging a warning.

    Parameters
    ----------
    raw:
        The raw LLM response string.

    Returns
    -------
    Tuple of ``(RelevanceGrade, float)`` where the float is in [0.0, 1.0].
    """
    grade = RelevanceGrade.BAD
    score = 0.0

    grade_match = _GRADE_RE.search(raw)
    if grade_match:
        grade_str = grade_match.group(1).lower()
        grade = _GRADE_MAP.get(grade_str, RelevanceGrade.BAD)
    else:
        logger.warning("Could not parse GRADE from grading response: %r", raw[:200])

    score_match = _SCORE_RE.search(raw)
    if score_match:
        try:
            score = float(score_match.group(1))
            score = max(0.0, min(1.0, score))  # clamp to [0, 1]
        except ValueError:
            logger.warning("Invalid SCORE value in grading response: %r", raw[:200])
    else:
        # Infer score from grade when no explicit score is given
        score_fallbacks = {
            RelevanceGrade.GOOD: 0.9,
            RelevanceGrade.NEED_WEB: 0.5,
            RelevanceGrade.BAD: 0.1,
        }
        score = score_fallbacks.get(grade, 0.0)
        logger.debug(
            "No SCORE in grading response; using grade-based fallback %.1f.", score
        )

    return grade, score


__all__ = [
    "render_relevance_grading_prompt",
    "parse_grading_response",
]
