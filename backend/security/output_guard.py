"""
security/output_guard.py

Validates generated answers before returning them to the caller.

Checks:
  1. Every ``Citation`` has a non-empty ``chunk_id``, ``document_id``, and a
     plausible ``score`` in [0, 1].
  2. When citations are present, answer sentences that contain no backed claim
     are flagged as ``unverified_claims``.

Returns an ``OutputGuardResult`` — never raises, so a buggy guard doesn't
block the API response.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional

from app.models import Citation
from app.config import SecuritySettings, get_settings

logger = logging.getLogger(__name__)

# Minimum plausible citation score
_MIN_PLAUSIBLE_SCORE = 0.0
_MAX_PLAUSIBLE_SCORE = 1.0


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class OutputGuardResult:
    """Result of an output verification pass."""

    is_valid: bool
    unverified_claims: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# OutputGuard
# ---------------------------------------------------------------------------

class OutputGuard:
    """
    Verifies LLM-generated answers for citation completeness and plausibility.

    Parameters
    ----------
    settings:
        Override ``SecuritySettings`` (mainly for testing).
    """

    def __init__(self, settings: Optional[SecuritySettings] = None) -> None:
        self._cfg: SecuritySettings = settings or get_settings().security

    def verify(
        self,
        answer: str,
        citations: List[Citation],
    ) -> OutputGuardResult:
        """
        Verify *answer* against *citations*.

        Returns an ``OutputGuardResult`` — never raises.

        Parameters
        ----------
        answer:
            The generated answer text.
        citations:
            The citations produced alongside the answer.
        """
        if not self._cfg.enable_output_guard:
            return OutputGuardResult(is_valid=True)

        try:
            return self._run_verification(answer, citations)
        except Exception as exc:  # noqa: BLE001
            logger.error("OutputGuard.verify raised unexpectedly: %s", exc, exc_info=True)
            return OutputGuardResult(is_valid=True)

    def _run_verification(
        self,
        answer: str,
        citations: List[Citation],
    ) -> OutputGuardResult:
        warnings: List[str] = []
        is_valid = True

        # 1. Check citation field completeness and score plausibility
        for cit in citations:
            if not cit.chunk_id:
                warnings.append(f"Citation {cit.citation_id!r} has an empty chunk_id.")
                is_valid = False
            if not cit.document_id:
                warnings.append(f"Citation {cit.citation_id!r} has an empty document_id.")
                is_valid = False
            if not (_MIN_PLAUSIBLE_SCORE <= cit.score <= _MAX_PLAUSIBLE_SCORE):
                warnings.append(
                    f"Citation {cit.citation_id!r} has implausible score {cit.score}."
                )
                is_valid = False

        # 2. Flag sentences with no backing citation
        unverified: List[str] = []
        if citations:
            # Build a set of text snippets for rough coverage check
            citation_snippets = {
                cit.text_snippet.strip().lower()[:80] for cit in citations
            }
            sentences = self._split_sentences(answer)
            for sentence in sentences:
                if not sentence.strip():
                    continue
                if not self._sentence_is_backed(sentence, citation_snippets):
                    unverified.append(sentence)

            if unverified:
                logger.debug(
                    "OutputGuard: %d sentence(s) have no direct citation backing.",
                    len(unverified),
                )

        return OutputGuardResult(
            is_valid=is_valid,
            unverified_claims=unverified,
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        """Split text into sentences on [.!?] boundaries."""
        return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]

    @staticmethod
    def _sentence_is_backed(sentence: str, snippets: set) -> bool:
        """
        Heuristic: a sentence is considered backed if any citation snippet
        shares at least one 4-gram with the sentence (case-insensitive).
        """
        sent_lower = sentence.lower()
        words = sent_lower.split()
        if len(words) < 4:
            # Very short sentences — assume backed to avoid noisy flagging
            return True

        sentence_ngrams = {
            " ".join(words[i : i + 4]) for i in range(len(words) - 3)
        }

        for snippet in snippets:
            snippet_words = snippet.split()
            snippet_ngrams = {
                " ".join(snippet_words[i : i + 4])
                for i in range(len(snippet_words) - 3)
            }
            if sentence_ngrams & snippet_ngrams:
                return True

        return False


__all__ = ["OutputGuard", "OutputGuardResult"]
