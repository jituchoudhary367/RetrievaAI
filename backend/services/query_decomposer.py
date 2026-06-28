"""
services/query_decomposer.py

Decomposes compound queries into simpler sub-queries via an LLM call.

Gated by ``FeatureFlags.enable_query_decomposition``:
  - When the flag is OFF, returns ``[query]`` unchanged (no-op).
  - When the query doesn't look compound, returns ``[query]`` unchanged.
  - Otherwise, calls the LLM with ``render_decomposition_prompt`` and parses
    the numbered list response into individual sub-queries.
"""

from __future__ import annotations

import logging
import re
from typing import List, Optional

from app.config import LLMSettings, get_settings
from prompts.templates import render_decomposition_prompt

logger = logging.getLogger(__name__)

# Heuristics for "compound query" detection
_COMPOUND_PATTERNS = [
    re.compile(r"\b(and|also|additionally|furthermore|as well as)\b", re.I),
    re.compile(r"\?.*\?"),  # multiple question marks
    re.compile(r"(compare|contrast|difference between|both)\b", re.I),
    re.compile(r"(part 1|step 1|first.*second|list.*explain)", re.I),
]

# Parse numbered list output from LLM
_NUMBERED_LINE_RE = re.compile(r"^\s*\d+[\.\)]\s*(.+)$", re.MULTILINE)


class QueryDecomposer:
    """
    Decomposes compound queries into simpler, independent sub-queries.

    Parameters
    ----------
    llm_settings:
        Override ``LLMSettings`` (mainly for testing).
    """

    def __init__(self, llm_settings: Optional[LLMSettings] = None) -> None:
        cfg = get_settings()
        self._cfg: LLMSettings = llm_settings or cfg.llm
        self._feature_flags = cfg.features

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def decompose(self, query: str) -> List[str]:
        """
        Decompose *query* into sub-queries.

        Returns ``[query]`` when:
          - ``enable_query_decomposition`` is False, or
          - the query doesn't appear compound.

        Otherwise returns a list of ≥1 sub-queries.
        """
        if not self._feature_flags.enable_query_decomposition:
            logger.debug("Query decomposition disabled by feature flag.")
            return [query]

        if not self._looks_compound(query):
            logger.debug("Query does not appear compound; skipping decomposition.")
            return [query]

        try:
            return self._decompose_with_llm(query)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Query decomposition failed: %s — returning original query.", exc)
            return [query]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _looks_compound(query: str) -> bool:
        """Heuristic check: return True if query looks multi-part."""
        return any(p.search(query) for p in _COMPOUND_PATTERNS)

    def _decompose_with_llm(self, query: str) -> List[str]:
        prompt = render_decomposition_prompt(query)
        raw = self._call_llm(prompt)
        if not raw:
            return [query]

        sub_queries = self._parse_numbered_list(raw)
        if not sub_queries:
            logger.warning("LLM returned unparseable decomposition; using original.")
            return [query]

        # Cap at 5 sub-queries
        sub_queries = sub_queries[:5]
        logger.info(
            "Decomposed query into %d sub-queries: %s",
            len(sub_queries),
            sub_queries,
        )
        return sub_queries

    def _call_llm(self, prompt: str) -> Optional[str]:
        """Minimal LLM invocation returning raw text."""
        try:
            cfg = get_settings()
            provider = cfg.llm.provider.value
            api_key = cfg.resolved_llm_api_key()

            if provider == "anthropic":
                import anthropic  # noqa: PLC0415
                client = anthropic.Anthropic(api_key=api_key)
                msg = client.messages.create(
                    model=self._cfg.model_name,
                    max_tokens=256,
                    messages=[{"role": "user", "content": prompt}],
                )
                return msg.content[0].text if msg.content else None

            if provider == "openai":
                import openai  # noqa: PLC0415
                oc = openai.OpenAI(api_key=api_key)
                resp = oc.chat.completions.create(
                    model=self._cfg.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=256,
                )
                return resp.choices[0].message.content

            logger.warning("QueryDecomposer: unsupported LLM provider %s.", provider)
            return None

        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"LLM call failed: {exc}") from exc

    @staticmethod
    def _parse_numbered_list(raw: str) -> List[str]:
        """Extract items from a numbered list in *raw*."""
        matches = _NUMBERED_LINE_RE.findall(raw)
        return [m.strip() for m in matches if m.strip()]


__all__ = ["QueryDecomposer"]
