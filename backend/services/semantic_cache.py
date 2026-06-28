"""
services/semantic_cache.py

Redis-backed semantic query cache.

Cache lookups are similarity-based rather than exact-string-match: the query
is embedded and compared (cosine similarity) against cached query embeddings.
A hit is returned when similarity ≥ ``RedisSettings.cache_similarity_threshold``.

Embeddings are stored alongside the serialised ``ChatResponse`` under a
``RedisSettings.cache_key_prefix``-prefixed key.  Both expire at
``cache_ttl_seconds``.

``redis`` is lazily imported so the module is importable without the library.
"""

from __future__ import annotations

import json
import logging
import math
from typing import Dict, List, Optional

from app.config import RedisSettings, get_settings
from pipeline.embedder import Embedder
from app.models import ChatResponse

logger = logging.getLogger(__name__)


class SemanticCache:
    """
    Semantic (embedding-similarity) query cache backed by Redis.

    Parameters
    ----------
    embedder:
        Embedder used to vectorise queries.  Defaults to a new ``Embedder``.
    settings:
        Override ``RedisSettings`` (mainly for testing).
    """

    def __init__(
        self,
        embedder: Optional[Embedder] = None,
        settings: Optional[RedisSettings] = None,
    ) -> None:
        cfg = get_settings()
        self._cfg: RedisSettings = settings or cfg.redis
        self._embedder = embedder or Embedder()
        self._client = None  # Lazy init

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, query: str) -> Optional[ChatResponse]:
        """
        Return a cached ``ChatResponse`` for *query*, or ``None`` on miss.

        Performs a cosine-similarity scan over stored query embeddings.
        """
        client = self._get_client()
        if client is None:
            return None

        try:
            query_emb = self._embed(query)
            if query_emb is None:
                return None

            # Scan all embedding keys
            prefix = self._cfg.cache_key_prefix + "emb:"
            cursor = 0
            best_key: Optional[str] = None
            best_sim = -1.0

            while True:
                cursor, keys = client.scan(cursor, match=prefix + "*", count=100)
                for key in keys:
                    raw_emb = client.get(key)
                    if raw_emb is None:
                        continue
                    cached_emb = [float(v) for v in raw_emb.split(",")]
                    sim = _cosine_similarity(query_emb, cached_emb)
                    if sim > best_sim:
                        best_sim = sim
                        best_key = key
                if cursor == 0:
                    break

            if best_key is None or best_sim < self._cfg.cache_similarity_threshold:
                logger.debug(
                    "SemanticCache miss (best_sim=%.3f < threshold=%.3f).",
                    best_sim,
                    self._cfg.cache_similarity_threshold,
                )
                return None

            # Retrieve the response stored under the matching response key
            resp_key = best_key.replace(prefix, self._cfg.cache_key_prefix + "resp:")
            raw_resp = client.get(resp_key)
            if raw_resp is None:
                return None

            response = ChatResponse.model_validate_json(raw_resp)
            logger.info(
                "SemanticCache HIT (sim=%.3f, key=%s).", best_sim, best_key
            )
            return response

        except Exception as exc:  # noqa: BLE001
            logger.warning("SemanticCache.get failed: %s", exc)
            return None

    def set(self, query: str, response: ChatResponse) -> None:
        """
        Store *response* in the cache, keyed by the embedding of *query*.
        """
        client = self._get_client()
        if client is None:
            return

        try:
            query_emb = self._embed(query)
            if query_emb is None:
                return

            import hashlib  # noqa: PLC0415
            cache_id = hashlib.sha256(query.encode()).hexdigest()[:16]
            emb_key = self._cfg.cache_key_prefix + "emb:" + cache_id
            resp_key = self._cfg.cache_key_prefix + "resp:" + cache_id
            ttl = self._cfg.cache_ttl_seconds

            emb_value = ",".join(str(v) for v in query_emb)
            resp_value = response.model_dump_json(by_alias=True)

            if ttl > 0:
                client.setex(emb_key, ttl, emb_value)
                client.setex(resp_key, ttl, resp_value)
            else:
                client.set(emb_key, emb_value)
                client.set(resp_key, resp_value)

            logger.debug("SemanticCache SET key=%s.", cache_id)

        except Exception as exc:  # noqa: BLE001
            logger.warning("SemanticCache.set failed: %s", exc)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_client(self) -> Optional[object]:
        if self._client is not None:
            return self._client
        try:
            import redis as redis_lib  # noqa: PLC0415
            self._client = redis_lib.Redis.from_url(
                self._cfg.url,
                socket_timeout=self._cfg.socket_timeout,
                socket_connect_timeout=self._cfg.socket_connect_timeout,
                decode_responses=True,
            )
            self._client.ping()
            return self._client
        except ImportError:
            logger.warning(
                "redis not installed — SemanticCache disabled. "
                "Install with: pip install redis"
            )
            return None
        except Exception as exc:  # noqa: BLE001
            logger.warning("SemanticCache: could not connect to Redis: %s", exc)
            return None

    def _embed(self, text: str) -> Optional[List[float]]:
        try:
            return self._embedder.embed_texts([text])[0]
        except Exception as exc:  # noqa: BLE001
            logger.warning("SemanticCache: embedding failed: %s", exc)
            return None


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


__all__ = ["SemanticCache"]
