"""
services/query_router.py

Lightweight intent classifier that maps a user query to a ``QueryIntent``
enum value.

Strategy: rule-based heuristics (keyword matching + pattern scoring).  This
is intentionally simple and fast — no LLM call required.  The classifier is
accurate enough for routing purposes; individual pipeline stages perform
deeper analysis if needed.

Intent → routing:
  CODE_SEARCH   — queries about code symbols, functions, classes, repos
  WEB_SEARCH    — queries about current events, news, prices, live data
  HYBRID_SEARCH — queries combining knowledge-base and external info
  COMPLEX_QA    — multi-part or analytical questions
  SIMPLE_QA     — everything else
"""

from __future__ import annotations

import logging
import re
from typing import List, Optional

from app.models import QueryIntent, ChatMessage

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pattern tables
# ---------------------------------------------------------------------------

_CODE_PATTERNS = [
    re.compile(r"\b(function|class|method|module|import|package|library|repo|repository)\b", re.I),
    re.compile(r"\b(python|javascript|typescript|golang|rust|java|c\+\+|kotlin|swift)\b", re.I),
    re.compile(r"\b(code|implement|debug|error|exception|stack trace|syntax|algorithm)\b", re.I),
    re.compile(r"def\s+\w+|class\s+\w+|import\s+\w+", re.I),
]

_WEB_PATTERNS = [
    re.compile(r"\b(today|now|current|latest|recent|news|live|real[ -]?time|up[ -]?to[ -]?date)\b", re.I),
    re.compile(r"\b(price|stock|weather|score|election|trending)\b", re.I),
    re.compile(r"\b(what (is|are) the (current|latest|new))\b", re.I),
]

_COMPLEX_PATTERNS = [
    re.compile(r"\b(compare|analyse|analyze|evaluate|discuss|explain in detail|summarise|summarize)\b", re.I),
    re.compile(r"\b(pros and cons|trade[ -]?offs?|advantages|disadvantages)\b", re.I),
    re.compile(r"(why|how).*and.*(why|how)", re.I),
    re.compile(r"\?.*\?"),  # multiple question marks
]

_HYBRID_PATTERNS = [
    re.compile(r"\b(combine|mix|both|also include|along with)\b", re.I),
]


# ---------------------------------------------------------------------------
# QueryRouter
# ---------------------------------------------------------------------------

class QueryRouter:
    """
    Rule-based query intent classifier.

    ``route()`` assigns a ``QueryIntent`` based on keyword/pattern scoring.
    Conversation history can influence routing (e.g. a follow-up to a code
    question may itself be treated as a code question).
    """

    def route(
        self,
        query: str,
        history: Optional[List[ChatMessage]] = None,
    ) -> QueryIntent:
        """
        Classify *query* into a ``QueryIntent``.

        Parameters
        ----------
        query:
            The user's current query string.
        history:
            Recent conversation history (used for context, not heavily weighted).
        """
        code_score = self._score(query, _CODE_PATTERNS)
        web_score = self._score(query, _WEB_PATTERNS)
        complex_score = self._score(query, _COMPLEX_PATTERNS)
        hybrid_score = self._score(query, _HYBRID_PATTERNS)

        # Context boost from recent history
        if history:
            last_content = " ".join(
                m.content for m in history[-4:] if m.content
            )
            code_score += self._score(last_content, _CODE_PATTERNS) * 0.3

        logger.debug(
            "QueryRouter scores — code=%.2f web=%.2f complex=%.2f hybrid=%.2f",
            code_score,
            web_score,
            complex_score,
            hybrid_score,
        )

        # Decision logic (thresholds are heuristic)
        if code_score >= 2:
            intent = QueryIntent.CODE_SEARCH
        elif web_score >= 2:
            intent = QueryIntent.WEB_SEARCH
        elif hybrid_score >= 1 and (code_score >= 1 or web_score >= 1):
            intent = QueryIntent.HYBRID_SEARCH
        elif complex_score >= 2:
            intent = QueryIntent.COMPLEX_QA
        else:
            intent = QueryIntent.SIMPLE_QA

        logger.info("QueryRouter: %r → %s", query[:80], intent.value)
        return intent

    @staticmethod
    def _score(text: str, patterns: List[re.Pattern]) -> float:
        """Return the number of patterns that match *text*."""
        return sum(1.0 for p in patterns if p.search(text))


__all__ = ["QueryRouter"]
