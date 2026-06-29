"""
security/input_guard.py

Input validation and sanitisation guard applied before retrieval.

Checks (in order):
  1. Query length against ``SecuritySettings.max_query_length``
  2. PII pattern detection (toggle via ``pii_detection_enabled``)
     - Email addresses
     - US/international phone numbers
     - US Social Security Numbers
     - Credit card numbers (Luhn-like pattern)
  3. Prompt-injection heuristic scoring against ``prompt_injection_threshold``

Raises ``SecurityError`` on any violation.
"""

from __future__ import annotations

import logging
import re
from typing import List, Optional, Tuple
import time

from redis.asyncio import Redis
from app.config import SecuritySettings, get_settings
from app.models import QueryRequest, TenantContext
from services.tenant_registry import registry

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Domain error
# ---------------------------------------------------------------------------

class SecurityError(Exception):
    """Raised when a security check fails."""


# ---------------------------------------------------------------------------
# PII patterns
# ---------------------------------------------------------------------------

_PII_PATTERNS: List[Tuple[str, re.Pattern]] = [
    (
        "email",
        re.compile(
            r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
            re.IGNORECASE,
        ),
    ),
    (
        "phone",
        re.compile(
            r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b"
        ),
    ),
    (
        "ssn",
        re.compile(r"\b\d{3}[-\s]\d{2}[-\s]\d{4}\b"),
    ),
    (
        "credit_card",
        re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
    ),
]

# ---------------------------------------------------------------------------
# Prompt injection heuristics
# ---------------------------------------------------------------------------
# Each entry: (pattern, weight)  — weights are accumulated; if total >= threshold
# the request is rejected.

_INJECTION_PATTERNS: List[Tuple[re.Pattern, float]] = [
    (re.compile(r"ignore (all |previous |prior )?(instructions?|prompts?|rules?|guidelines?)", re.I), 0.9),
    (re.compile(r"you are now", re.I), 0.4),
    (re.compile(r"(act|pretend|roleplay) as", re.I), 0.3),
    (re.compile(r"(disregard|forget|override) (your|all|any) (instructions?|rules?|guidelines?|training)", re.I), 0.9),
    (re.compile(r"system prompt", re.I), 0.5),
    (re.compile(r"jailbreak", re.I), 0.9),
    (re.compile(r"DAN\b", re.I), 0.7),
    (re.compile(r"do anything now", re.I), 0.8),
    (re.compile(r"output (your|the) (system|initial|original) prompt", re.I), 0.9),
    (re.compile(r"reveal (your|the) (instructions?|prompt|rules?)", re.I), 0.7),
    (re.compile(r"<\|.*?\|>"), 0.6),  # token injection patterns
    (re.compile(r"\[INST\]|\[/INST\]|\[SYS\]"), 0.7),
]


# ---------------------------------------------------------------------------
# InputGuard
# ---------------------------------------------------------------------------

class InputGuard:
    """
    Validates a ``QueryRequest`` before it enters the retrieval pipeline.

    Parameters
    ----------
    settings:
        Override ``SecuritySettings`` (mainly for testing).
    """

    def __init__(self, redis_client: Redis, settings: Optional[SecuritySettings] = None) -> None:
        self._cfg: SecuritySettings = settings or get_settings().security
        self._redis = redis_client

    async def validate(self, request: QueryRequest, tenant_context: TenantContext) -> None:
        """
        Validate *request*.  Raises ``SecurityError`` on any violation.
        Rate limits based on tenant_id.
        """
        await self._check_rate_limit(tenant_context)
        self._check_length(request.query)
        if self._cfg.pii_detection_enabled:
            self._check_pii(request.query)
        self._check_injection(request.query)

    # ------------------------------------------------------------------
    # Checks
    # ------------------------------------------------------------------
    
    async def _check_rate_limit(self, tenant_context: TenantContext) -> None:
        tenant_config = await registry.get_tenant_config(tenant_context.tenant_id)
        limit = tenant_config.rate_limit_requests_per_minute or self._cfg.rate_limit_requests_per_minute
        
        if limit <= 0:
            return  # No limit
            
        current_minute = int(time.time() / 60)
        key = f"{tenant_context.tenant_id}:rate_limit:{current_minute}"
        
        current_count = await self._redis.incr(key)
        if current_count == 1:
            await self._redis.expire(key, 60)
            
        if current_count > limit:
            raise SecurityError(f"Rate limit exceeded. Maximum {limit} requests per minute allowed.")

    def _check_length(self, query: str) -> None:
        if len(query) > self._cfg.max_query_length:
            raise SecurityError(
                f"Query length {len(query)} exceeds maximum allowed "
                f"{self._cfg.max_query_length} characters."
            )

    def _check_pii(self, query: str) -> None:
        detected: List[str] = []
        for label, pattern in _PII_PATTERNS:
            if pattern.search(query):
                detected.append(label)
        if detected:
            logger.warning("PII detected in query: %s", detected)
            raise SecurityError(
                f"Query contains potential PII ({', '.join(detected)}). "
                "Please remove sensitive information before submitting."
            )

    def _check_injection(self, query: str) -> None:
        total_score = 0.0
        for pattern, weight in _INJECTION_PATTERNS:
            if pattern.search(query):
                total_score += weight
                if total_score >= self._cfg.prompt_injection_threshold:
                    logger.warning(
                        "Prompt injection detected (score=%.2f ≥ threshold=%.2f).",
                        total_score,
                        self._cfg.prompt_injection_threshold,
                    )
                    raise SecurityError(
                        "Query was flagged as a potential prompt-injection attempt "
                        "and has been blocked."
                    )


__all__ = ["InputGuard", "SecurityError"]
