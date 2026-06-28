"""
pipeline/preprocessor.py

Cleans raw extracted text before it enters the chunking stage.

Responsibilities:
  - HTML-entity unescaping (&amp; → &, etc.)
  - Residual HTML tag stripping (handles cases where an extractor left markup)
  - Unicode NFKC normalization (decomposed characters → composed forms)
  - Control-character stripping (null bytes, form feeds, etc.)
  - Repeated-line (running header/footer) removal via configurable frequency
    threshold
  - Whitespace collapse (consecutive blank lines → one blank line; trailing
    spaces stripped)

No third-party dependencies — stdlib only.
"""

from __future__ import annotations

import html
import logging
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from typing import List

logger = logging.getLogger(__name__)

# Regex that matches any HTML/XML-like tag
_TAG_RE = re.compile(r"<[^>]+>")

# Control characters except tab (0x09), LF (0x0A), and CR (0x0D)
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# Three or more consecutive blank lines → two blank lines (i.e., one gap)
_EXCESSIVE_BLANK_RE = re.compile(r"\n{3,}")

# Default: lines appearing more than this fraction of total lines are treated
# as running headers/footers and removed.
_DEFAULT_REPEAT_THRESHOLD = 0.05


@dataclass
class PreprocessResult:
    """Output of ``Preprocessor.process()``."""

    text: str
    removed_boilerplate_lines: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class Preprocessor:
    """
    Stateless text cleaner applied immediately after extraction.

    Parameters
    ----------
    repeat_threshold:
        Lines that appear more frequently than this fraction of the total
        line count are removed as running headers/footers.  Set to ``1.0``
        to disable.
    min_line_length_for_repeat_check:
        Very short lines (e.g. page numbers) are skip-checked; only lines
        longer than this threshold are candidates for repeated-line removal.
    """

    def __init__(
        self,
        repeat_threshold: float = _DEFAULT_REPEAT_THRESHOLD,
        min_line_length_for_repeat_check: int = 5,
    ) -> None:
        self.repeat_threshold = repeat_threshold
        self.min_line_length_for_repeat_check = min_line_length_for_repeat_check

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(self, text: str) -> PreprocessResult:
        """
        Clean *text* and return a ``PreprocessResult``.

        Steps applied in order:
        1. HTML-entity unescape
        2. Residual tag strip
        3. Unicode NFKC normalize
        4. Control-char strip
        5. Repeated-line removal
        6. Whitespace collapse
        """
        warnings: List[str] = []

        if not text:
            return PreprocessResult(text="", warnings=["Input text was empty."])

        # 1. HTML-entity unescape
        text = html.unescape(text)

        # 2. Residual tag strip
        text, tag_count = self._strip_tags(text)
        if tag_count:
            logger.debug("Stripped %d residual HTML tag(s) from text.", tag_count)

        # 3. NFKC normalization
        text = unicodedata.normalize("NFKC", text)

        # 4. Control-char strip
        text = _CONTROL_CHAR_RE.sub("", text)

        # 5. Repeated-line removal
        text, removed = self._remove_repeated_lines(text)

        # 6. Whitespace collapse
        text = self._collapse_whitespace(text)

        if not text.strip():
            warnings.append("After preprocessing, text is empty.")

        return PreprocessResult(
            text=text,
            removed_boilerplate_lines=removed,
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _strip_tags(text: str) -> tuple[str, int]:
        matches = _TAG_RE.findall(text)
        count = len(matches)
        cleaned = _TAG_RE.sub("", text)
        return cleaned, count

    def _remove_repeated_lines(self, text: str) -> tuple[str, List[str]]:
        lines = text.split("\n")
        if not lines:
            return text, []

        # Count only lines long enough to be real content
        eligible = [
            ln.strip()
            for ln in lines
            if len(ln.strip()) >= self.min_line_length_for_repeat_check
        ]
        if not eligible:
            return text, []

        freq = Counter(eligible)
        total = len(eligible)
        threshold_count = max(2, int(total * self.repeat_threshold))

        boilerplate: set[str] = {
            ln for ln, cnt in freq.items() if cnt >= threshold_count
        }

        if not boilerplate:
            return text, []

        removed: List[str] = sorted(boilerplate)
        cleaned_lines = [
            ln for ln in lines if ln.strip() not in boilerplate
        ]
        logger.debug(
            "Removed %d repeated boilerplate line(s): %s",
            len(removed),
            removed[:5],
        )
        return "\n".join(cleaned_lines), removed

    @staticmethod
    def _collapse_whitespace(text: str) -> str:
        # Strip trailing spaces from each line
        lines = [line.rstrip() for line in text.split("\n")]
        text = "\n".join(lines)
        # Collapse 3+ consecutive newlines to 2
        text = _EXCESSIVE_BLANK_RE.sub("\n\n", text)
        return text.strip()


__all__ = ["Preprocessor", "PreprocessResult"]
