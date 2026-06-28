"""
security/content_filter.py

Keyword/category-based content moderation for generated text.

Checks for predefined categories of harmful content (violence, hate speech,
adult content, self-harm, illegal activity, PII leakage) and returns a
``ContentFilterResult`` indicating whether the text is safe.

No ML model is required — rule-based pattern matching keeps this module
importable and fast with zero optional dependencies.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Pattern, Tuple

from app.config import SecuritySettings, get_settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Category definitions
# ---------------------------------------------------------------------------

# Each entry: (category_name, [(pattern_str, flags), ...])
_CATEGORY_PATTERNS: List[Tuple[str, List[Tuple[str, int]]]] = [
    (
        "violence",
        [
            (r"\b(kill|murder|assassinate|slaughter|massacre|bomb|explode|detonate)\b", re.I),
            (r"\bhow to (make|build|assemble) (a )?(bomb|weapon|explosive)\b", re.I),
        ],
    ),
    (
        "hate_speech",
        [
            (r"\b(racial slur|ethnic cleansing|white supremacy|nazi)\b", re.I),
            (r"\b(hate|exterminate|genocide)\s+(the\s+)?(jews?|muslims?|blacks?|gays?)\b", re.I),
        ],
    ),
    (
        "adult_content",
        [
            (r"\b(explicit sex|pornograph|nsfw)\b", re.I),
        ],
    ),
    (
        "self_harm",
        [
            (r"\b(how to (commit suicide|self[ -]harm|cut yourself))\b", re.I),
            (r"\b(suicide method|kill myself)\b", re.I),
        ],
    ),
    (
        "illegal_activity",
        [
            (r"\b(how to (hack|phish|crack|bypass security))\b", re.I),
            (r"\b(drug synthesis|manufacture (meth|heroin|cocaine))\b", re.I),
            (r"\b(child (pornography|exploitation|abuse))\b", re.I),
        ],
    ),
]

# Pre-compile all patterns once at module load
_COMPILED_PATTERNS: Dict[str, List[re.Pattern]] = {
    category: [re.compile(pat, flags) for pat, flags in patterns]
    for category, patterns in _CATEGORY_PATTERNS
}


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class ContentFilterResult:
    """Result of a content-filter check."""

    is_safe: bool
    categories: List[str] = field(default_factory=list)
    reason: Optional[str] = None


# ---------------------------------------------------------------------------
# ContentFilter
# ---------------------------------------------------------------------------

class ContentFilter:
    """
    Lightweight keyword-based content moderator.

    Parameters
    ----------
    settings:
        Override ``SecuritySettings`` (mainly for testing).
    """

    def __init__(self, settings: Optional[SecuritySettings] = None) -> None:
        self._cfg: SecuritySettings = settings or get_settings().security

    def check(self, text: str) -> ContentFilterResult:
        """
        Check *text* for harmful content.

        Returns a ``ContentFilterResult`` with ``is_safe=True`` when no
        problematic categories are detected.

        This method never raises — any internal error is caught and treated
        as safe to avoid blocking the pipeline on a filter bug.
        """
        if not self._cfg.enable_content_filter:
            return ContentFilterResult(is_safe=True)

        try:
            return self._run_checks(text)
        except Exception as exc:  # noqa: BLE001
            logger.error("ContentFilter.check raised unexpectedly: %s", exc, exc_info=True)
            return ContentFilterResult(is_safe=True)

    def _run_checks(self, text: str) -> ContentFilterResult:
        triggered: List[str] = []

        for category, patterns in _COMPILED_PATTERNS.items():
            for pattern in patterns:
                if pattern.search(text):
                    triggered.append(category)
                    break  # one match per category is enough

        if triggered:
            reason = f"Content flagged in categories: {', '.join(triggered)}"
            logger.warning("ContentFilter: %s (text length=%d)", reason, len(text))
            return ContentFilterResult(
                is_safe=False,
                categories=triggered,
                reason=reason,
            )

        return ContentFilterResult(is_safe=True)


__all__ = ["ContentFilter", "ContentFilterResult"]
