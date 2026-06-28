"""
retrieval/filters.py

Translates ``app.models.MetadataFilter`` objects into Qdrant filter trees.

Supports all operators defined on ``MetadataFilter``:
  eq, ne, gt, gte, lt, lte, in, not_in, contains

``qdrant_client`` is imported lazily so this module is importable even if the
library is not installed (the function itself will raise an ImportError with a
clear pip-install hint if called without the dependency).
"""

from __future__ import annotations

import logging
from typing import List, Optional

from app.models import MetadataFilter

logger = logging.getLogger(__name__)


class RetrievalError(Exception):
    """Raised when a retrieval-layer operation fails."""


def build_qdrant_filter(
    filters: List[MetadataFilter],
) -> Optional[object]:
    """
    Translate a list of ``MetadataFilter`` objects into a Qdrant
    ``Filter`` object, or ``None`` when *filters* is empty.

    Parameters
    ----------
    filters:
        List of ``MetadataFilter`` instances to combine with AND semantics.

    Returns
    -------
    A ``qdrant_client.http.models.Filter`` instance, or ``None``.

    Raises
    ------
    ImportError  if ``qdrant-client`` is not installed.
    RetrievalError  if an unsupported operator is encountered.
    """
    if not filters:
        return None

    try:
        from qdrant_client.http.models import (  # noqa: PLC0415
            Filter,
            FieldCondition,
            MatchValue,
            MatchAny,
            MatchExcept,
            Range,
        )
    except ImportError as exc:
        raise ImportError(
            "qdrant-client is required for filter building. "
            "Install it with: pip install qdrant-client"
        ) from exc

    conditions: List[object] = []

    for f in filters:
        condition = _build_condition(f, FieldCondition, MatchValue, MatchAny, MatchExcept, Range)
        if condition is not None:
            conditions.append(condition)

    if not conditions:
        return None

    return Filter(must=conditions)


def _build_condition(
    f: MetadataFilter,
    FieldCondition: object,
    MatchValue: object,
    MatchAny: object,
    MatchExcept: object,
    Range: object,
) -> Optional[object]:
    """Build a single Qdrant ``FieldCondition`` from one ``MetadataFilter``."""
    op = f.operator
    key = f.field
    val = f.value

    if op == "eq":
        return FieldCondition(key=key, match=MatchValue(value=val))

    if op == "ne":
        # Qdrant: must_not [MatchValue]
        from qdrant_client.http.models import Filter  # noqa: PLC0415
        return Filter(
            must_not=[FieldCondition(key=key, match=MatchValue(value=val))]
        )

    if op == "gt":
        return FieldCondition(key=key, range=Range(gt=val))

    if op == "gte":
        return FieldCondition(key=key, range=Range(gte=val))

    if op == "lt":
        return FieldCondition(key=key, range=Range(lt=val))

    if op == "lte":
        return FieldCondition(key=key, range=Range(lte=val))

    if op == "in":
        values = list(val) if not isinstance(val, list) else val
        return FieldCondition(key=key, match=MatchAny(any=values))

    if op == "not_in":
        values = list(val) if not isinstance(val, list) else val
        return FieldCondition(key=key, match=MatchExcept(**{"except": values}))

    if op == "contains":
        # Qdrant full-text match (substring)
        from qdrant_client.http.models import MatchText  # noqa: PLC0415
        return FieldCondition(key=key, match=MatchText(text=str(val)))

    raise RetrievalError(f"Unsupported filter operator: {op!r}")


__all__ = ["build_qdrant_filter", "RetrievalError"]
