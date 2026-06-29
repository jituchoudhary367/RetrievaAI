"""
pipeline/embedder.py

Converts text chunks into dense embedding vectors.

Provider backends (all optional; lazily imported):
  openai              → EmbeddingProvider.OPENAI
  sentence-transformers → EmbeddingProvider.HUGGINGFACE
  cohere              → EmbeddingProvider.COHERE

Features:
  - Pluggable embedding cache (InMemoryEmbeddingCache default,
    RedisEmbeddingCache when Redis is available) keyed by SHA-256 of
    (model_name, text).
  - Exponential-backoff retry up to EmbeddingSettings.max_retries.
  - Batch processing at EmbeddingSettings.batch_size.
  - Optional L2-normalisation of output vectors.
"""

from __future__ import annotations

import hashlib
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Sequence

from app.config import EmbeddingProvider, EmbeddingSettings, get_settings
from app.models import Chunk

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Domain error
# ---------------------------------------------------------------------------

class EmbeddingError(Exception):
    """Raised when embedding generation fails after all retries."""


# ---------------------------------------------------------------------------
# Cache ABC + implementations
# ---------------------------------------------------------------------------

class EmbeddingCache(ABC):
    """Abstract cache for embedding vectors."""

    @abstractmethod
    def get(self, key: str) -> Optional[List[float]]:
        """Return cached embedding for *key*, or ``None`` on miss."""

    @abstractmethod
    def set(self, key: str, embedding: List[float]) -> None:
        """Store *embedding* under *key*."""


class InMemoryEmbeddingCache(EmbeddingCache):
    """Simple in-process dict cache.  Not shared across workers."""

    def __init__(self) -> None:
        self._store: Dict[str, List[float]] = {}

    def get(self, key: str) -> Optional[List[float]]:
        return self._store.get(key)

    def set(self, key: str, embedding: List[float]) -> None:
        self._store[key] = embedding

    def __len__(self) -> int:
        return len(self._store)


class RedisEmbeddingCache(EmbeddingCache):
    """
    Redis-backed embedding cache.

    Embeddings are stored as newline-joined float strings under a TTL
    derived from ``RedisSettings.cache_ttl_seconds``.
    """

    def __init__(self) -> None:
        settings = get_settings()
        ttl = settings.redis.cache_ttl_seconds
        prefix = settings.redis.cache_key_prefix + "emb:"

        try:
            import redis as redis_lib  # noqa: PLC0415
            self._client = redis_lib.Redis.from_url(
                settings.redis.url,
                socket_timeout=settings.redis.socket_timeout,
                socket_connect_timeout=settings.redis.socket_connect_timeout,
                decode_responses=True,
            )
        except ImportError as exc:
            raise ImportError(
                "redis is required for RedisEmbeddingCache. "
                "Install it with: pip install redis"
            ) from exc

        self._ttl = ttl
        self._prefix = prefix

    def get(self, key: str) -> Optional[List[float]]:
        try:
            raw = self._client.get(self._prefix + key)
            if raw is None:
                return None
            return [float(v) for v in raw.split(",")]
        except Exception as exc:  # noqa: BLE001
            logger.warning("RedisEmbeddingCache.get failed: %s", exc)
            return None

    def set(self, key: str, embedding: List[float]) -> None:
        try:
            value = ",".join(str(v) for v in embedding)
            self._client.setex(self._prefix + key, self._ttl, value)
        except Exception as exc:  # noqa: BLE001
            logger.warning("RedisEmbeddingCache.set failed: %s", exc)


# ---------------------------------------------------------------------------
# Embedder
# ---------------------------------------------------------------------------

class Embedder:
    """
    Converts texts to dense embedding vectors using the configured provider.

    Parameters
    ----------
    cache:
        An ``EmbeddingCache`` implementation.  Defaults to
        ``InMemoryEmbeddingCache``.
    settings:
        Override ``EmbeddingSettings`` (mainly for testing).
    """

    def __init__(
        self,
        cache: Optional[EmbeddingCache] = None,
        settings: Optional[EmbeddingSettings] = None,
    ) -> None:
        self._cfg: EmbeddingSettings = settings or get_settings().embedding
        self._cache: EmbeddingCache = cache or InMemoryEmbeddingCache()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def embed_chunks(self, chunks: List[Chunk]) -> List[Chunk]:
        """
        Embed all *chunks*, mutating ``.embedding`` in place.

        Returns the same list for convenience.
        """
        texts = [chunk.text for chunk in chunks]
        embeddings = self.embed_texts(texts)
        for chunk, emb in zip(chunks, embeddings):
            chunk.embedding = emb
        logger.info("Embedded %d chunks.", len(chunks))
        return chunks

    def embed_texts(self, texts: Sequence[str]) -> List[List[float]]:
        """
        Embed a sequence of texts, respecting the cache and batch size.

        Returns a list of embedding vectors in the same order as *texts*.
        """
        if not texts:
            return []

        results: List[Optional[List[float]]] = [None] * len(texts)
        uncached_indices: List[int] = []

        if self._cfg.cache_embeddings:
            for i, text in enumerate(texts):
                key = self._cache_key(text)
                cached = self._cache.get(key)
                if cached is not None:
                    results[i] = cached
                else:
                    uncached_indices.append(i)
        else:
            uncached_indices = list(range(len(texts)))

        if uncached_indices:
            uncached_texts = [texts[i] for i in uncached_indices]
            fresh = self._batch_embed(uncached_texts)
            for idx, emb in zip(uncached_indices, fresh):
                results[idx] = emb
                if self._cfg.cache_embeddings:
                    self._cache.set(self._cache_key(texts[idx]), emb)

        # Narrow type — all slots filled
        return [r for r in results if r is not None]

    # ------------------------------------------------------------------
    # Batching + retry
    # ------------------------------------------------------------------

    def _batch_embed(self, texts: List[str]) -> List[List[float]]:
        batch_size = self._cfg.batch_size
        all_embeddings: List[List[float]] = []
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            embeddings = self._embed_with_retry(batch)
            all_embeddings.extend(embeddings)
        return all_embeddings

    def _embed_with_retry(self, texts: List[str]) -> List[List[float]]:
        last_exc: Exception = RuntimeError("No attempts made")
        for attempt in range(self._cfg.max_retries + 1):
            try:
                embeddings = self._call_provider(texts)
                if self._cfg.normalize:
                    embeddings = [self._l2_normalize(e) for e in embeddings]
                return embeddings
            except EmbeddingError:
                raise
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                wait = self._cfg.retry_backoff_seconds * (2 ** attempt)
                logger.warning(
                    "Embedding attempt %d/%d failed: %s — retrying in %.1fs",
                    attempt + 1,
                    self._cfg.max_retries + 1,
                    exc,
                    wait,
                )
                if attempt < self._cfg.max_retries:
                    time.sleep(wait)
        raise EmbeddingError(
            f"Embedding failed after {self._cfg.max_retries + 1} attempt(s)"
        ) from last_exc

    # ------------------------------------------------------------------
    # Provider dispatch
    # ------------------------------------------------------------------

    def _call_provider(self, texts: List[str]) -> List[List[float]]:
        provider = self._cfg.provider
        if provider == EmbeddingProvider.OPENAI:
            return self._embed_openai(texts)
        if provider == EmbeddingProvider.HUGGINGFACE:
            return self._embed_huggingface(texts)
        if provider == EmbeddingProvider.COHERE:
            return self._embed_cohere(texts)
        raise EmbeddingError(f"Unknown embedding provider: {provider}")

    def _embed_openai(self, texts: List[str]) -> List[List[float]]:
        try:
            import openai  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "openai is required for OpenAI embedding provider. "
                "Install it with: pip install openai"
            ) from exc

        api_key = get_settings().resolved_embedding_api_key()
        client = openai.OpenAI(
            api_key=api_key,
            timeout=self._cfg.request_timeout,
        )
        try:
            response = client.embeddings.create(
                model=self._cfg.model_name,
                input=texts,
            )
            return [item.embedding for item in response.data]
        except Exception as exc:
            raise EmbeddingError(f"OpenAI embedding failed: {exc}") from exc

    def _embed_huggingface(self, texts: List[str]) -> List[List[float]]:
        try:
            from sentence_transformers import SentenceTransformer  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "sentence-transformers is required for HuggingFace embedding provider. "
                "Install it with: pip install sentence-transformers"
            ) from exc

        try:
            model = SentenceTransformer(self._cfg.model_name)
            embeddings = model.encode(texts, convert_to_numpy=True)
            return [list(map(float, e)) for e in embeddings]
        except Exception as exc:
            raise EmbeddingError(f"HuggingFace embedding failed: {exc}") from exc

    def _embed_cohere(self, texts: List[str]) -> List[List[float]]:
        try:
            import cohere  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "cohere is required for Cohere embedding provider. "
                "Install it with: pip install cohere"
            ) from exc

        api_key = get_settings().resolved_embedding_api_key()
        try:
            co = cohere.Client(api_key=api_key)
            response = co.embed(
                texts=texts,
                model=self._cfg.model_name,
                input_type="search_document",
            )
            return [list(map(float, e)) for e in response.embeddings]
        except Exception as exc:
            raise EmbeddingError(f"Cohere embedding failed: {exc}") from exc

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def _cache_key(self, text: str) -> str:
        # Note: tenant_id is explicitly EXCLUDED from this cache key. 
        # This preserves cross-tenant cache hits for identical public data.
        payload = f"{self._cfg.model_name}:{text}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _l2_normalize(vector: List[float]) -> List[float]:
        import math
        norm = math.sqrt(sum(v * v for v in vector))
        if norm == 0:
            return vector
        return [v / norm for v in vector]


__all__ = [
    "Embedder",
    "EmbeddingError",
    "EmbeddingCache",
    "InMemoryEmbeddingCache",
    "RedisEmbeddingCache",
]
