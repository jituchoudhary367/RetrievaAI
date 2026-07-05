"""
app/models.py

Shared request/response schemas for the RAG application.

Every route, service, and tool that crosses an API boundary (HTTP request,
HTTP response, SSE stream chunk, or inter-service call) should import its
data shape from here rather than redefining ad-hoc dicts or local classes.
This keeps the contract between `routes/`, `services/`, and `retrieval/`
explicit, typed, and validated in one place.

Conventions:
    - All public API models inherit from `APIModel` (camelCase aliases,
      `from_attributes` enabled so they can be built from ORM-like objects).
    - All internal-only models inherit from `InternalModel` (no aliasing,
      used purely between modules and never serialized directly to a client).
    - Enums are `str` subclasses so they serialize cleanly to JSON and are
      directly comparable to plain strings.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator, EmailStr


# --------------------------------------------------------------------------- #
# Base classes
# --------------------------------------------------------------------------- #

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid.uuid4())


def _to_camel(snake: str) -> str:
    first, *rest = snake.split("_")
    return first + "".join(word.capitalize() for word in rest)


class APIModel(BaseModel):
    """Base class for models that cross the public HTTP boundary."""

    model_config = ConfigDict(
        alias_generator=_to_camel,
        populate_by_name=True,
        from_attributes=True,
        extra="forbid",
        str_strip_whitespace=True,
        protected_namespaces=(),
    )


class InternalModel(BaseModel):
    """Base class for models passed between internal services only."""

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        arbitrary_types_allowed=True,
    )


# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #

class QueryIntent(str, Enum):
    SIMPLE_QA = "simple_qa"
    COMPLEX_QA = "complex_qa"
    CODE_SEARCH = "code_search"
    WEB_SEARCH = "web_search"
    HYBRID_SEARCH = "hybrid_search"


class RelevanceGrade(str, Enum):
    GOOD = "good"
    BAD = "bad"
    NEED_WEB = "need_web"


class RetrievalSource(str, Enum):
    VECTOR = "vector"
    BM25 = "bm25"
    WEB = "web"
    CODE = "code"
    CACHE = "cache"


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class StreamEventType(str, Enum):
    START = "start"
    TOKEN = "token"
    CITATION = "citation"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    ERROR = "error"
    END = "end"


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


# --------------------------------------------------------------------------- #
# Conversation primitives
# --------------------------------------------------------------------------- #

class ChatMessage(APIModel):
    """A single turn in a conversation."""

    role: MessageRole
    content: str = Field(..., min_length=1, max_length=32_000)
    timestamp: datetime = Field(default_factory=_utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Request models
# --------------------------------------------------------------------------- #

class MetadataFilter(APIModel):
    """Generic metadata filter applied during retrieval."""

    field: str = Field(..., min_length=1)
    value: Any
    operator: str = Field(
        default="eq",
        description="One of: eq, ne, gt, gte, lt, lte, in, not_in, contains",
    )

    @field_validator("operator")
    @classmethod
    def _validate_operator(cls, v: str) -> str:
        allowed = {"eq", "ne", "gt", "gte", "lt", "lte", "in", "not_in", "contains"}
        if v not in allowed:
            raise ValueError(f"operator must be one of {sorted(allowed)}")
        return v


class QueryRequest(APIModel):
    """Request body for POST /api/query (the conversational RAG endpoint)."""

    query: str = Field(..., min_length=1, max_length=4000)
    session_id: Optional[str] = Field(default=None)
    conversation_history: List[ChatMessage] = Field(default_factory=list)
    filters: List[MetadataFilter] = Field(default_factory=list)
    top_k: int = Field(default=5, ge=1, le=50)
    stream: bool = Field(default=True)
    use_cache: bool = Field(default=True)
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1, le=8000)

    # §1.10 — three new optional fields that make chat controls functional.
    # model_override is validated against an allow-list before being passed to LLM.
    model_override: Optional[str] = Field(
        default=None,
        description="Override the default LLM model (validated against allow-list)",
    )
    retrieval_mode: Optional[str] = Field(
        default="hybrid",
        description="One of: hybrid, vector, keyword. Controls which retrieval legs to use.",
    )
    force_web_search: bool = Field(
        default=False,
        description="Treat as a manual web-search trigger alongside CRAG's automatic one.",
    )

    @field_validator("query")
    @classmethod
    def _strip_and_validate_query(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("query must not be empty or whitespace-only")
        return v

    @field_validator("retrieval_mode")
    @classmethod
    def _validate_retrieval_mode(cls, v: Optional[str]) -> Optional[str]:
        allowed = {"hybrid", "vector", "keyword"}
        if v is not None and v not in allowed:
            raise ValueError(f"retrieval_mode must be one of {sorted(allowed)}")
        return v

    @model_validator(mode="after")
    def _ensure_session_id(self) -> "QueryRequest":
        if not self.session_id:
            self.session_id = _new_id()
        return self


class SearchRequest(APIModel):
    """Request body for POST /api/search (retrieval-only, no LLM call)."""

    query: str = Field(..., min_length=1, max_length=4000)
    top_k: int = Field(default=10, ge=1, le=100)
    filters: List[MetadataFilter] = Field(default_factory=list)
    rerank: bool = Field(default=True)
    include_debug_info: bool = Field(default=False)

    @field_validator("query")
    @classmethod
    def _strip_query(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("query must not be empty or whitespace-only")
        return v


# --------------------------------------------------------------------------- #
# Retrieval / response models
# --------------------------------------------------------------------------- #

class Citation(APIModel):
    """A single citation backing a claim in the generated answer."""

    citation_id: str = Field(default_factory=lambda: _new_id()[:8])
    document_id: str
    chunk_id: str
    source: str = Field(..., description="Human-readable source, e.g. filename or URL")
    text_snippet: str = Field(..., max_length=1000)
    score: float = Field(..., ge=0.0, le=1.0)
    page_number: Optional[int] = Field(default=None, ge=0)
    url: Optional[str] = Field(default=None)


class RetrievedChunk(InternalModel):
    """A single chunk returned from the retrieval layer, pre-rerank."""

    chunk_id: str
    document_id: str
    text: str
    source: RetrievalSource
    dense_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    sparse_score: Optional[float] = Field(default=None, ge=0.0)
    fused_score: Optional[float] = Field(default=None)
    rerank_score: Optional[float] = Field(default=None)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchResult(APIModel):
    """A single ranked result returned by the /api/search endpoint."""

    chunk_id: str
    document_id: str
    text: str
    score: float = Field(..., ge=0.0, le=1.0)
    source: RetrievalSource
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchResponse(APIModel):
    """Response body for POST /api/search."""

    query: str
    results: List[SearchResult]
    total_results: int = Field(..., ge=0)
    latency_ms: float = Field(..., ge=0.0)
    debug_info: Optional[Dict[str, Any]] = Field(default=None)

    @model_validator(mode="after")
    def _total_matches_results_when_unset(self) -> "SearchResponse":
        if self.total_results == 0 and self.results:
            self.total_results = len(self.results)
        return self


class TokenUsage(APIModel):
    """Token accounting for a single LLM call."""

    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def _compute_total(self) -> "TokenUsage":
        computed = self.prompt_tokens + self.completion_tokens
        if self.total_tokens == 0:
            self.total_tokens = computed
        return self


class ResponseMetadata(APIModel):
    """Out-of-band metadata accompanying a chat response."""

    intent: Optional[QueryIntent] = Field(default=None)
    used_cache: bool = Field(default=False)
    used_web_search: bool = Field(default=False)
    used_code_search: bool = Field(default=False)
    crag_corrections: int = Field(default=0, ge=0)
    retrieval_latency_ms: Optional[float] = Field(default=None, ge=0.0)
    generation_latency_ms: Optional[float] = Field(default=None, ge=0.0)
    total_latency_ms: Optional[float] = Field(default=None, ge=0.0)
    token_usage: Optional[TokenUsage] = Field(default=None)
    model_name: Optional[str] = Field(default=None)
    # §1.10 — three new additive fields surfacing retrieval counts the
    # HybridRetriever and Reranker already compute internally.
    retrieved_count: int = Field(default=0, ge=0)
    reranked_count: int = Field(default=0, ge=0)
    top_k: int = Field(default=5, ge=0)


class ChatResponse(APIModel):
    """Response body for POST /api/query (non-streaming mode)."""

    session_id: str
    answer: str
    citations: List[Citation] = Field(default_factory=list)
    metadata: ResponseMetadata = Field(default_factory=ResponseMetadata)
    created_at: datetime = Field(default_factory=_utcnow)


# --------------------------------------------------------------------------- #
# Streaming models
# --------------------------------------------------------------------------- #

class StreamChunk(APIModel):
    """A single Server-Sent-Events payload emitted while streaming an answer."""

    event: StreamEventType
    session_id: str
    sequence: int = Field(..., ge=0)
    delta: Optional[str] = Field(default=None)
    citation: Optional[Citation] = Field(default=None)
    tool_name: Optional[str] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    metadata: Optional[ResponseMetadata] = Field(default=None)

    def to_sse(self) -> str:
        """Serialize as a `data: <json>\\n\\n` SSE frame."""
        return f"data: {self.model_dump_json(by_alias=True, exclude_none=True)}\n\n"


# --------------------------------------------------------------------------- #
# Error model
# --------------------------------------------------------------------------- #

class ErrorDetail(APIModel):
    code: str
    message: str
    field: Optional[str] = Field(default=None)


class ErrorResponse(APIModel):
    """Standard error envelope returned by exception handlers."""

    request_id: str = Field(default_factory=_new_id)
    status_code: int
    errors: List[ErrorDetail]
    timestamp: datetime = Field(default_factory=_utcnow)


# --------------------------------------------------------------------------- #
# Health models
# --------------------------------------------------------------------------- #

class ComponentHealth(APIModel):
    name: str
    status: HealthStatus
    latency_ms: Optional[float] = Field(default=None, ge=0.0)
    detail: Optional[str] = Field(default=None)


class HealthResponse(APIModel):
    """Response body for /health, /ready, /live."""

    status: HealthStatus
    version: str
    uptime_seconds: float = Field(..., ge=0.0)
    components: List[ComponentHealth] = Field(default_factory=list)

    @model_validator(mode="after")
    def _derive_overall_status(self) -> "HealthResponse":
        if not self.components:
            return self
        statuses = {c.status for c in self.components}
        if HealthStatus.UNHEALTHY in statuses:
            self.status = HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            self.status = HealthStatus.DEGRADED
        else:
            self.status = HealthStatus.HEALTHY
        return self


# --------------------------------------------------------------------------- #
# Ingestion / document models (used by pipeline + indexer, surfaced via
# debug endpoints)
# --------------------------------------------------------------------------- #

class DocumentMetadata(InternalModel):
    document_id: str = Field(default_factory=_new_id)
    user_id: str = Field(default="")
    source_path: str
    source_type: str = Field(
        ..., description="One of: pdf, html, docx, image, text, md, csv, json"
    )
    title: Optional[str] = Field(default=None)
    author: Optional[str] = Field(default=None)
    created_at: Optional[datetime] = Field(default=None)
    language: Optional[str] = Field(default=None)
    tags: List[str] = Field(default_factory=list)
    extra: Dict[str, Any] = Field(default_factory=dict)


class Chunk(InternalModel):
    chunk_id: str = Field(default_factory=_new_id)
    document_id: str
    user_id: str = Field(default="")
    text: str
    chunk_index: int = Field(..., ge=0)
    token_count: Optional[int] = Field(default=None, ge=0)
    embedding: Optional[List[float]] = Field(default=None)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("text")
    @classmethod
    def _non_empty_text(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("chunk text must not be empty")
        return v


# --------------------------------------------------------------------------- #
# Auth models
# --------------------------------------------------------------------------- #

class SignupRequest(APIModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8)
    tenant_name: str = Field(..., min_length=1)


class LoginRequest(APIModel):
    email: str
    password: str = Field(..., min_length=8)


class SignupResponse(BaseModel):
    userId: str
    email: str
    message: str = "Signup successful. Please check your email to verify your account."


class MessageResponse(BaseModel):
    message: str

PermissionErrorAlias = type("PermissionErrorAlias", (Exception,), {})


class VerifyEmailRequest(BaseModel):
    token: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class RequestPasswordResetRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    newPassword: str = Field(..., min_length=8)


class InviteRequest(BaseModel):
    email: EmailStr
    role: str = Field(pattern="^(member|admin|viewer)$")


class AcceptInviteRequest(APIModel):
    token: str
    password: str = Field(..., min_length=8)


class RefreshRequest(APIModel):
    refresh_token: str


class AuthResponse(APIModel):
    access_token: str
    refresh_token: str
    expires_in: int
    user_id: str
    roles: List[str]


class InviteResponse(APIModel):
    invite_link: str
    expires_at: datetime
