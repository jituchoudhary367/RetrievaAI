"""
pipeline/deduplicator.py

Deduplication layer applied after preprocessing, before chunking.

Two strategies:
  1. Exact deduplication  — SHA-256 hash of normalised text.
  2. Near-duplicate detection — pure-Python 64-bit SimHash + Hamming distance
     threshold (no third-party dependency; O(n) fingerprinting per document).

The public ``compute_content_hash`` function is also consumed by
``pipeline/ingest.py`` to build the idempotency manifest that prevents
re-ingesting unchanged files.
"""

from __future__ import annotations

import hashlib
import logging
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Callable, Generic, List, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Number of bits in the SimHash fingerprint
_SIMHASH_BITS = 64
# Maximum Hamming distance to be considered a near-duplicate
_DEFAULT_HAMMING_THRESHOLD = 3


# ---------------------------------------------------------------------------
# Public hash utility (also used by ingest.py manifest)
# ---------------------------------------------------------------------------

def compute_content_hash(text: str) -> str:
    """Return the SHA-256 hex digest of *text* after light normalisation.

    Normalisation applied: Unicode NFKC, lower-case, whitespace collapse.
    This ensures that trivial formatting differences (e.g. different line
    endings) do not produce different hashes for semantically identical
    documents.
    """
    normalised = _normalise_for_hash(text)
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class DedupResult(Generic[T]):
    """Output of ``Deduplicator.deduplicate()``."""

    kept: List[T] = field(default_factory=list)
    exact_duplicates: List[T] = field(default_factory=list)
    near_duplicates: List[T] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Deduplicator
# ---------------------------------------------------------------------------

class Deduplicator:
    """
    Removes exact and near-duplicate items from a sequence.

    Parameters
    ----------
    hamming_threshold:
        Maximum Hamming distance between two SimHash fingerprints that still
        counts as a near-duplicate.  Larger values are more aggressive.
        Set to ``0`` to disable near-duplicate detection entirely.
    """

    def __init__(self, hamming_threshold: int = _DEFAULT_HAMMING_THRESHOLD) -> None:
        self.hamming_threshold = hamming_threshold

    def deduplicate(
        self,
        items: List[T],
        text_fn: Callable[[T], str],
    ) -> DedupResult[T]:
        """
        Deduplicate *items* using *text_fn* to extract the comparable text.

        Parameters
        ----------
        items:
            The sequence to deduplicate (list of any type).
        text_fn:
            A callable that, given one item, returns the text to compare.

        Returns
        -------
        DedupResult with ``kept``, ``exact_duplicates``, and
        ``near_duplicates`` populated.
        """
        result: DedupResult[T] = DedupResult()
        seen_hashes: set[str] = set()
        kept_fingerprints: List[int] = []

        for item in items:
            text = text_fn(item)
            content_hash = compute_content_hash(text)

            # --- Exact duplicate check ---
            if content_hash in seen_hashes:
                logger.debug("Exact duplicate found; skipping item.")
                result.exact_duplicates.append(item)
                continue
            seen_hashes.add(content_hash)

            # --- Near-duplicate check via SimHash ---
            if self.hamming_threshold > 0:
                fp = _simhash(text)
                if self._is_near_duplicate(fp, kept_fingerprints):
                    logger.debug(
                        "Near-duplicate found (Hamming ≤ %d); skipping item.",
                        self.hamming_threshold,
                    )
                    result.near_duplicates.append(item)
                    continue
                kept_fingerprints.append(fp)

            result.kept.append(item)

        logger.info(
            "Dedup: kept=%d  exact_dupes=%d  near_dupes=%d",
            len(result.kept),
            len(result.exact_duplicates),
            len(result.near_duplicates),
        )
        return result

    def _is_near_duplicate(
        self, fingerprint: int, kept: List[int]
    ) -> bool:
        for existing in kept:
            if _hamming_distance(fingerprint, existing) <= self.hamming_threshold:
                return True
        return False


# ---------------------------------------------------------------------------
# SimHash implementation (pure Python, 64-bit)
# ---------------------------------------------------------------------------

def _normalise_for_hash(text: str) -> str:
    """Light normalisation for deterministic hashing."""
    text = unicodedata.normalize("NFKC", text).lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _simhash(text: str, bits: int = _SIMHASH_BITS) -> int:
    """
    Compute a 64-bit SimHash fingerprint for *text*.

    Algorithm:
    1. Tokenise into overlapping 3-shingles (character trigrams).
    2. Hash each shingle with MD5 (first ``bits`` bits).
    3. Accumulate a bit-weight vector: +1 if the bit is set, -1 otherwise.
    4. Final fingerprint: 1 where weight > 0, else 0.
    """
    text = _normalise_for_hash(text)
    if not text:
        return 0

    weights = [0] * bits
    shingles = _shingles(text, n=3)

    for shingle in shingles:
        h = int(hashlib.md5(shingle.encode("utf-8")).hexdigest(), 16)  # 128-bit
        # Use only the first `bits` bits
        for i in range(bits):
            bit = (h >> (127 - i)) & 1
            weights[i] += 1 if bit else -1

    fingerprint = 0
    for i, w in enumerate(weights):
        if w > 0:
            fingerprint |= 1 << (bits - 1 - i)

    return fingerprint


def _shingles(text: str, n: int = 3) -> List[str]:
    """Return all character n-grams of *text*."""
    if len(text) < n:
        return [text]
    return [text[i : i + n] for i in range(len(text) - n + 1)]


def _hamming_distance(a: int, b: int) -> int:
    """Compute the Hamming distance between two integers."""
    xor = a ^ b
    return bin(xor).count("1")


__all__ = [
    "Deduplicator",
    "DedupResult",
    "compute_content_hash",
]
