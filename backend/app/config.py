"""
app/config.py

Centralized configuration management for the RAG application.

This is the FOUNDATION module — every other module (services, retrieval,
agents, pipeline, routes) must read configuration from here. Nothing else
in the codebase should hardcode environment-dependent values (hosts,
ports, model names, thresholds, feature flags, etc.).

Configuration precedence (highest first):
    1. Explicit process environment variables
    2. Values in a `.env` file at the project root
    3. Field defaults declared below

Usage:
    from app.config import get_settings
    settings = get_settings()
    redis_url = settings.redis.url
    if settings.features.enable_crag:
        ...
"""

from __future__ import annotations

from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #

class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
    OLLAMA = "ollama"


class EmbeddingProvider(str, Enum):
    OPENAI = "openai"
    HUGGINGFACE = "huggingface"
    COHERE = "cohere"


class LogFormat(str, Enum):
    JSON = "json"
    CONSOLE = "console"


class ChunkingStrategy(str, Enum):
    RECURSIVE = "recursive"
    SEMANTIC = "semantic"
    AST = "ast"
    MARKDOWN = "markdown"


# --------------------------------------------------------------------------- #
# Sub-settings groups
# --------------------------------------------------------------------------- #

class RedisSettings(BaseSettings):
    """Connection and semantic-cache configuration for Redis."""

    model_config = SettingsConfigDict(env_prefix="REDIS_", extra="ignore")

    host: str = Field(default="localhost")
    port: int = Field(default=6379, ge=1, le=65535)
    db: int = Field(default=0, ge=0)
    password: Optional[str] = Field(default=None, repr=False)
    ssl: bool = Field(default=False)
    socket_timeout: float = Field(default=5.0, gt=0)
    socket_connect_timeout: float = Field(default=5.0, gt=0)
    max_connections: int = Field(default=50, ge=1)
    health_check_interval: int = Field(default=30, ge=0)

    # Semantic cache specific
    cache_ttl_seconds: int = Field(default=3600, ge=0)
    cache_similarity_threshold: float = Field(default=0.95, ge=0.0, le=1.0)
    cache_key_prefix: str = Field(default="rag:cache:")

    @property
    def url(self) -> str:
        scheme = "rediss" if self.ssl else "redis"
        auth = f":{self.password}@" if self.password else ""
        return f"{scheme}://{auth}{self.host}:{self.port}/{self.db}"


class QdrantSettings(BaseSettings):
    """Connection and indexing configuration for Qdrant."""

    model_config = SettingsConfigDict(env_prefix="QDRANT_", extra="ignore")

    host: str = Field(default="localhost")
    port: int = Field(default=6333, ge=1, le=65535)
    grpc_port: int = Field(default=6334, ge=1, le=65535)
    use_grpc: bool = Field(default=True)
    prefer_grpc: bool = Field(default=True)
    api_key: Optional[str] = Field(default=None, repr=False)
    https: bool = Field(default=False)
    collection_name: str = Field(default="rag_documents")
    vector_size: int = Field(default=1536, ge=1)
    distance_metric: str = Field(default="Cosine")
    timeout: float = Field(default=30.0, gt=0)

    # HNSW index parameters
    hnsw_ef_construct: int = Field(default=128, ge=1)
    hnsw_m: int = Field(default=16, ge=1)
    hnsw_ef_search: int = Field(default=64, ge=1)

    # BM25 sparse index (kept alongside dense vectors for hybrid search)
    bm25_index_path: Path = Field(default=Path("./data/bm25_index"))

    @property
    def url(self) -> str:
        scheme = "https" if self.https else "http"
        return f"{scheme}://{self.host}:{self.port}"


class EmbeddingSettings(BaseSettings):
    """Embedding model provider and batching configuration."""

    model_config = SettingsConfigDict(env_prefix="EMBEDDING_", extra="ignore")

    provider: EmbeddingProvider = Field(default=EmbeddingProvider.OPENAI)
    model_name: str = Field(default="text-embedding-3-small")
    api_key: Optional[str] = Field(default=None, repr=False)
    dimensions: int = Field(default=1536, ge=1)
    batch_size: int = Field(default=64, ge=1, le=2048)
    max_retries: int = Field(default=3, ge=0)
    retry_backoff_seconds: float = Field(default=1.0, ge=0)
    request_timeout: float = Field(default=30.0, gt=0)
    cache_embeddings: bool = Field(default=True)
    normalize: bool = Field(default=True)


class LLMSettings(BaseSettings):
    """Primary LLM provider configuration, with optional fallback model."""

    model_config = SettingsConfigDict(env_prefix="LLM_", extra="ignore")

    provider: LLMProvider = Field(default=LLMProvider.ANTHROPIC)
    model_name: str = Field(default="claude-sonnet-4-6")
    api_key: Optional[str] = Field(default=None, repr=False)
    fallback_model_name: Optional[str] = Field(default=None)
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    timeout: float = Field(default=60.0, gt=0)
    max_retries: int = Field(default=3, ge=0)
    streaming: bool = Field(default=True)

    # Azure OpenAI specific (only used when provider == AZURE_OPENAI)
    azure_endpoint: Optional[str] = Field(default=None)
    azure_deployment: Optional[str] = Field(default=None)
    azure_api_version: Optional[str] = Field(default=None)


class ChunkingSettings(BaseSettings):
    """Document chunking strategy and sizing."""

    model_config = SettingsConfigDict(env_prefix="CHUNK_", extra="ignore")

    chunk_size: int = Field(default=800, ge=50)
    chunk_overlap: int = Field(default=100, ge=0)
    strategy: ChunkingStrategy = Field(default=ChunkingStrategy.RECURSIVE)
    min_chunk_size: int = Field(default=50, ge=1)
    max_chunk_size: int = Field(default=2000, ge=1)
    semantic_similarity_threshold: float = Field(default=0.5, ge=0.0, le=1.0)

    @field_validator("chunk_overlap")
    @classmethod
    def _overlap_smaller_than_size(cls, v: int, info) -> int:
        chunk_size = info.data.get("chunk_size", 800)
        if v >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        return v


class RetrievalSettings(BaseSettings):
    """Hybrid retrieval, fusion, and reranking parameters."""

    model_config = SettingsConfigDict(env_prefix="RETRIEVAL_", extra="ignore")

    top_k_dense: int = Field(default=20, ge=1)
    top_k_sparse: int = Field(default=20, ge=1)
    top_k_final: int = Field(default=5, ge=1)
    rrf_k: int = Field(default=60, ge=1)  # reciprocal rank fusion constant
    hybrid_alpha: float = Field(default=0.5, ge=0.0, le=1.0)  # dense vs sparse weight

    rerank_enabled: bool = Field(default=True)
    rerank_model: str = Field(default="cross-encoder/ms-marco-MiniLM-L-6-v2")
    rerank_top_n: int = Field(default=5, ge=1)

    similarity_score_threshold: float = Field(default=0.0, ge=0.0, le=1.0)


class CragSettings(BaseSettings):
    """Corrective-RAG grading thresholds and retry behavior."""

    model_config = SettingsConfigDict(env_prefix="CRAG_", extra="ignore")

    enabled: bool = Field(default=True)
    relevance_threshold_good: float = Field(default=0.7, ge=0.0, le=1.0)
    relevance_threshold_bad: float = Field(default=0.3, ge=0.0, le=1.0)
    max_correction_retries: int = Field(default=2, ge=0)
    web_search_fallback: bool = Field(default=True)
    code_search_fallback: bool = Field(default=True)

    @model_validator(mode="after")
    def _thresholds_consistent(self) -> "CragSettings":
        if self.relevance_threshold_bad >= self.relevance_threshold_good:
            raise ValueError(
                "relevance_threshold_bad must be lower than "
                "relevance_threshold_good"
            )
        return self


class DatabaseSettings(BaseSettings):
    """PostgreSQL connection configuration."""

    model_config = SettingsConfigDict(env_prefix="DB_", extra="ignore")

    host: str = Field(default="localhost")
    port: int = Field(default=5432, ge=1, le=65535)
    name: str = Field(default="rag_db")
    user: str = Field(default="rag_user")
    password: str = Field(default="rag_password", repr=False)
    pool_size: int = Field(default=10, ge=1)
    max_overflow: int = Field(default=20, ge=0)

    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

    @property
    def sync_url(self) -> str:
        """Synchronous URL for Alembic migrations."""
        return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class BlobStorageSettings(BaseSettings):
    """Local-filesystem blob storage for original uploaded files (§1.4)."""

    model_config = SettingsConfigDict(env_prefix="BLOB_", extra="ignore")

    root_path: Path = Field(default=Path("./data/blobs"))
    # backend: "local" (default) | "s3" (future)
    backend: str = Field(default="local")


class SecuritySettings(BaseSettings):
    """Input/output guardrails, rate limiting, and auth."""

    model_config = SettingsConfigDict(env_prefix="SECURITY_", extra="ignore")

    enable_input_guard: bool = Field(default=True)
    enable_output_guard: bool = Field(default=True)
    enable_content_filter: bool = Field(default=True)
    max_query_length: int = Field(default=4000, ge=1)
    rate_limit_requests_per_minute: int = Field(default=60, ge=1)
    pii_detection_enabled: bool = Field(default=True)
    prompt_injection_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    allowed_origins: List[str] = Field(default_factory=lambda: ["*"])
    jwt_secret_key: Optional[str] = Field(default="dev-secret-change-in-production", repr=False)
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=60, ge=1)
    jwt_refresh_token_expire_days: int = Field(default=30, ge=1)
    bcrypt_rounds: int = Field(default=12, ge=4, le=31)


class ObservabilitySettings(BaseSettings):
    """Logging, tracing, and metrics configuration."""

    model_config = SettingsConfigDict(env_prefix="OBSERVABILITY_", extra="ignore")

    log_level: str = Field(default="INFO")
    log_format: LogFormat = Field(default=LogFormat.JSON)
    enable_tracing: bool = Field(default=True)
    otel_exporter_endpoint: Optional[str] = Field(default=None)
    otel_service_name: str = Field(default="rag-service")
    enable_prometheus: bool = Field(default=True)
    prometheus_port: int = Field(default=9090, ge=1, le=65535)

    @field_validator("log_level")
    @classmethod
    def _validate_log_level(cls, v: str) -> str:
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in valid:
            raise ValueError(f"log_level must be one of {valid}")
        return upper


class ConversationSettings(BaseSettings):
    """Conversation memory window, summarization, and session TTL."""

    model_config = SettingsConfigDict(env_prefix="CONVERSATION_", extra="ignore")

    max_history_turns: int = Field(default=10, ge=1)
    max_history_tokens: int = Field(default=4000, ge=1)
    summarization_enabled: bool = Field(default=True)
    summarization_trigger_turns: int = Field(default=8, ge=1)
    session_ttl_seconds: int = Field(default=86400, ge=0)


class FeatureFlags(BaseSettings):
    """Toggle major pipeline capabilities without code changes."""

    model_config = SettingsConfigDict(env_prefix="FEATURE_", extra="ignore")

    enable_semantic_cache: bool = Field(default=True)
    enable_query_decomposition: bool = Field(default=True)
    enable_query_routing: bool = Field(default=True)
    enable_web_search_tool: bool = Field(default=True)
    enable_code_search_tool: bool = Field(default=True)
    enable_streaming: bool = Field(default=True)
    enable_reranking: bool = Field(default=True)
    enable_crag: bool = Field(default=True)


class TenancySettings(BaseSettings):
    """Multi-tenancy configuration and JWT claims mapping."""

    model_config = SettingsConfigDict(env_prefix="TENANCY_", extra="ignore")

    enabled: bool = Field(default=True)
    jwt_tenant_claim: str = Field(default="tenant_id")
    jwt_user_claim: str = Field(default="sub")
    jwt_roles_claim: str = Field(default="roles")
    default_tenant_id: Optional[str] = Field(default=None)
    tenant_id_payload_field: str = Field(default="tenant_id")
    registry_cache_ttl_seconds: int = Field(default=300, ge=0)


# --------------------------------------------------------------------------- #
# Root settings
# --------------------------------------------------------------------------- #

class Settings(BaseSettings):
    """
    Root application settings. Aggregates every sub-configuration group.

    Instantiate via `get_settings()`, not directly, so the parsed/validated
    instance is cached for the lifetime of the process.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Core application ---
    app_name: str = Field(default="production-rag")
    app_version: str = Field(default="0.1.0")
    environment: Environment = Field(default=Environment.DEVELOPMENT)
    debug: bool = Field(default=False)
    api_v1_prefix: str = Field(default="/api")
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, ge=1, le=65535)
    workers: int = Field(default=1, ge=1)

    # --- Filesystem paths ---
    base_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parent.parent
    )
    prompts_dir: Path = Field(default=Path("app/prompts"))
    data_dir: Path = Field(default=Path("data"))
    log_dir: Path = Field(default=Path("logs"))

    # --- Top-level API keys (convenience accessors; provider-specific
    #     settings below also expose an `api_key` field that takes
    #     precedence when set) ---
    anthropic_api_key: Optional[str] = Field(default=None, repr=False)
    openai_api_key: Optional[str] = Field(default=None, repr=False)
    cohere_api_key: Optional[str] = Field(default=None, repr=False)
    serper_api_key: Optional[str] = Field(default=None, repr=False)
    tavily_api_key: Optional[str] = Field(default=None, repr=False)

    # --- Sub-settings groups ---
    redis: RedisSettings = Field(default_factory=RedisSettings)
    qdrant: QdrantSettings = Field(default_factory=QdrantSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    blob: BlobStorageSettings = Field(default_factory=BlobStorageSettings)
    embedding: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    chunking: ChunkingSettings = Field(default_factory=ChunkingSettings)
    retrieval: RetrievalSettings = Field(default_factory=RetrievalSettings)
    crag: CragSettings = Field(default_factory=CragSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    observability: ObservabilitySettings = Field(default_factory=ObservabilitySettings)
    conversation: ConversationSettings = Field(default_factory=ConversationSettings)
    features: FeatureFlags = Field(default_factory=FeatureFlags)
    tenancy: TenancySettings = Field(default_factory=TenancySettings)

    # ----------------------------------------------------------------- #
    # Validators
    # ----------------------------------------------------------------- #

    @model_validator(mode="after")
    def _enforce_production_requirements(self) -> "Settings":
        """
        Fail fast at startup if a production deployment is missing
        required secrets or is running with unsafe defaults. This is
        intentionally strict: a misconfigured production deployment
        should refuse to boot rather than run insecurely.
        """
        if self.environment != Environment.PRODUCTION:
            return self

        if self.debug:
            raise ValueError("debug must be False when environment=production")

        if "*" in self.security.allowed_origins:
            raise ValueError(
                "Wildcard CORS origin '*' is not allowed when "
                "environment=production"
            )

        if self.llm.provider == LLMProvider.ANTHROPIC and not (
            self.anthropic_api_key or self.llm.api_key
        ):
            raise ValueError(
                "ANTHROPIC_API_KEY (or LLM_API_KEY) is required in production "
                "when LLM_PROVIDER=anthropic"
            )

        if self.llm.provider == LLMProvider.OPENAI and not (
            self.openai_api_key or self.llm.api_key
        ):
            raise ValueError(
                "OPENAI_API_KEY (or LLM_API_KEY) is required in production "
                "when LLM_PROVIDER=openai"
            )

        if self.embedding.provider == EmbeddingProvider.OPENAI and not (
            self.openai_api_key or self.embedding.api_key
        ):
            raise ValueError(
                "OPENAI_API_KEY (or EMBEDDING_API_KEY) is required in "
                "production when EMBEDDING_PROVIDER=openai"
            )

        if not self.security.jwt_secret_key:
            raise ValueError("SECURITY_JWT_SECRET_KEY is required in production")
            
        if self.tenancy.default_tenant_id is not None:
            raise ValueError("TENANCY_DEFAULT_TENANT_ID must not be set in production to avoid silent security bypasses")

        return self

    @model_validator(mode="after")
    def _ensure_directories_resolved(self) -> "Settings":
        """
        Resolve relative paths against base_dir so downstream modules
        never have to think about the current working directory.
        """
        if not self.prompts_dir.is_absolute():
            self.prompts_dir = (self.base_dir / self.prompts_dir).resolve()
        if not self.data_dir.is_absolute():
            self.data_dir = (self.base_dir / self.data_dir).resolve()
        if not self.log_dir.is_absolute():
            self.log_dir = (self.base_dir / self.log_dir).resolve()
        return self

    # ----------------------------------------------------------------- #
    # Convenience properties
    # ----------------------------------------------------------------- #

    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        return self.environment == Environment.DEVELOPMENT

    @property
    def is_test(self) -> bool:
        return self.environment == Environment.TEST

    def resolved_llm_api_key(self) -> Optional[str]:
        """Returns the effective API key for the configured LLM provider."""
        if self.llm.api_key:
            return self.llm.api_key
        return {
            LLMProvider.ANTHROPIC: self.anthropic_api_key,
            LLMProvider.OPENAI: self.openai_api_key,
        }.get(self.llm.provider)

    def resolved_embedding_api_key(self) -> Optional[str]:
        """Returns the effective API key for the configured embedding provider."""
        if self.embedding.api_key:
            return self.embedding.api_key
        return {
            EmbeddingProvider.OPENAI: self.openai_api_key,
            EmbeddingProvider.COHERE: self.cohere_api_key,
        }.get(self.embedding.provider)


# --------------------------------------------------------------------------- #
# Cached singleton accessor
# --------------------------------------------------------------------------- #

@lru_cache
def get_settings() -> Settings:
    """
    Returns a process-wide cached `Settings` instance.

    All application code should call this function rather than
    instantiating `Settings()` directly — this avoids re-parsing
    environment variables and re-running validators on every access,
    and guarantees every module sees the same configuration.

    To reload configuration (e.g. in tests), call `get_settings.cache_clear()`
    before calling `get_settings()` again.
    """
    return Settings()


# Module-level convenience instance. Importing `settings` directly is
# acceptable in application code; tests should prefer `get_settings()`
# together with `get_settings.cache_clear()` for isolation.
settings = get_settings()