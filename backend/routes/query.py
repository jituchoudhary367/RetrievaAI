"""
routes/query.py

FastAPI router for retrieval and generation endpoints.

Endpoints:
  POST /api/v1/query   — Standard non-streaming RAG query
  POST /api/v1/stream  — Streaming RAG query (Server-Sent Events)

Uses the ``RAGPipeline`` facade to execute the pipeline.
Dual-writes chat history to Postgres Conversation tables (§1.10).
"""

from __future__ import annotations

import asyncio
import logging
from typing import AsyncGenerator
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import QueryRequest, ChatResponse, ErrorResponse, StreamChunk
from services.rag_pipeline import RAGPipeline
from security.input_guard import SecurityError
from retrieval.filters import RetrievalError
from security.auth import get_current_user
from db.models.user import User
from db.engine import get_db, async_session_factory
from db.models.conversation import Conversation, ConversationMessage
from services.telemetry import record_query_event

logger = logging.getLogger(__name__)

router = APIRouter(tags=["query"])

def get_pipeline() -> RAGPipeline:
    return RAGPipeline()


async def _persist_conversation(
    tenant_id: str,
    user_id: str,
    session_id: str,
    user_query: str,
    assistant_response: str
) -> None:
    """Dual-write chat history to Postgres (fire-and-forget)."""
    try:
        async with async_session_factory() as db:
            result = await db.execute(
                select(Conversation).where(
                    Conversation.session_id == session_id,
                    Conversation.user_id == user_id
                )
            )
            conv = result.scalar_one_or_none()
            if not conv:
                title = user_query[:50] + "..." if len(user_query) > 50 else user_query
                conv = Conversation(
                    session_id=session_id,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    title=title,
                )
                db.add(conv)
                await db.flush()
            
            conv.updated_at = datetime.utcnow()
            
            db.add(ConversationMessage(
                conversation_id=conv.id,
                role="user",
                content=user_query
            ))
            
            db.add(ConversationMessage(
                conversation_id=conv.id,
                role="assistant",
                content=assistant_response
            ))
            
            await db.commit()
    except Exception as e:
        logger.warning(f"Failed to persist conversation to DB: {e}")


@router.post(
    "/query",
    response_model=ChatResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Validation or security error"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Execute a RAG query (non-streaming)",
)
async def execute_query(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
    pipeline: RAGPipeline = Depends(get_pipeline),
) -> ChatResponse:
    """
    Execute the full RAG pipeline and return a complete ``ChatResponse``.
    """
    logger.info("Received /query request for session %s from user %s", request.session_id, current_user.id)
    
    # Enforce tenant isolation on filters
    from app.models import MetadataFilter
    tenant_filter = MetadataFilter(key="tenant_id", value=current_user.tenant_id)
    if request.filters:
        request.filters.append(tenant_filter)
    else:
        request.filters = [tenant_filter]

    try:
        # Pass user roles to pipeline if needed for RBAC in retrieval, though tenant_id is the primary hard boundary.
        response = pipeline.run(request)
        
        # Dual-write conversation to Postgres
        asyncio.create_task(_persist_conversation(
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            session_id=request.session_id,
            user_query=request.query,
            assistant_response=response.answer
        ))
        
        # Fire and forget telemetry
        asyncio.create_task(record_query_event(
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            session_id=request.session_id,
            query_text=request.query,
            intent=response.metadata.intent.value if response.metadata.intent else None,
            used_cache=response.metadata.used_cache,
            used_web_search=response.metadata.used_web_search,
            used_code_search=response.metadata.used_code_search,
            crag_corrections=response.metadata.crag_corrections,
            retrieval_latency_ms=response.metadata.retrieval_latency_ms,
            generation_latency_ms=response.metadata.generation_latency_ms,
            total_latency_ms=response.metadata.total_latency_ms,
            prompt_tokens=response.metadata.token_usage.prompt_tokens if response.metadata.token_usage else 0,
            completion_tokens=response.metadata.token_usage.completion_tokens if response.metadata.token_usage else 0,
            total_tokens=response.metadata.token_usage.total_tokens if response.metadata.token_usage else 0,
            retrieved_count=response.metadata.retrieved_count,
            reranked_count=response.metadata.reranked_count,
            top_k=response.metadata.top_k,
            model_name=response.metadata.model_name,
            citations=[{"document_id": c.document_id, "source": c.source, "score": c.score} for c in response.citations]
        ))

        return response
    except SecurityError as exc:
        logger.warning("SecurityError on /query: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RetrievalError as exc:
        logger.warning("RetrievalError on /query: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Unexpected error on /query: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post(
    "/stream",
    responses={
        400: {"model": ErrorResponse, "description": "Validation or security error"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Execute a RAG query (streaming SSE)",
)
async def execute_query_stream(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
    pipeline: RAGPipeline = Depends(get_pipeline),
) -> StreamingResponse:
    """
    Execute the full RAG pipeline with streaming LLM output.
    """
    logger.info("Received /stream request for session %s from user %s", request.session_id, current_user.id)

    # Enforce tenant isolation on filters
    from app.models import MetadataFilter
    tenant_filter = MetadataFilter(key="tenant_id", value=current_user.tenant_id)
    if request.filters:
        request.filters.append(tenant_filter)
    else:
        request.filters = [tenant_filter]

    async def event_generator() -> AsyncGenerator[str, None]:
        full_response_text = ""
        metadata_chunk = None
        citations = []
        
        try:
            async for chunk in pipeline.stream(request):
                # Accumulate the response to persist after stream completes
                if chunk.event == "content":
                    full_response_text += chunk.content_delta or ""
                elif chunk.event == "metadata":
                    metadata_chunk = chunk
                elif chunk.event == "citation":
                    citations.append(chunk.citation)

                # SSE format: data: <json>\n\n
                yield f"data: {chunk.model_dump_json(by_alias=True)}\n\n"
                
            # Stream completed successfully. Fire off persistence and telemetry.
            asyncio.create_task(_persist_conversation(
                tenant_id=current_user.tenant_id,
                user_id=current_user.id,
                session_id=request.session_id,
                user_query=request.query,
                assistant_response=full_response_text
            ))
            
            if metadata_chunk and metadata_chunk.metadata:
                m = metadata_chunk.metadata
                tu = m.token_usage
                asyncio.create_task(record_query_event(
                    tenant_id=current_user.tenant_id,
                    user_id=current_user.id,
                    session_id=request.session_id,
                    query_text=request.query,
                    intent=m.intent.value if m.intent else None,
                    used_cache=m.used_cache,
                    used_web_search=m.used_web_search,
                    used_code_search=m.used_code_search,
                    crag_corrections=m.crag_corrections,
                    retrieval_latency_ms=m.retrieval_latency_ms,
                    generation_latency_ms=m.generation_latency_ms,
                    total_latency_ms=m.total_latency_ms,
                    prompt_tokens=tu.prompt_tokens if tu else 0,
                    completion_tokens=tu.completion_tokens if tu else 0,
                    total_tokens=tu.total_tokens if tu else 0,
                    retrieved_count=m.retrieved_count,
                    reranked_count=m.reranked_count,
                    top_k=m.top_k,
                    model_name=m.model_name,
                    citations=[{"document_id": c.document_id, "source": c.source, "score": c.score} for c in citations]
                ))

        except SecurityError as exc:
            logger.warning("SecurityError on /stream: %s", exc)
            err = StreamChunk(event="error", session_id=request.session_id, sequence=-1, error_message=str(exc))
            yield f"data: {err.model_dump_json(by_alias=True)}\n\n"
        except RetrievalError as exc:
            logger.warning("RetrievalError on /stream: %s", exc)
            err = StreamChunk(event="error", session_id=request.session_id, sequence=-1, error_message=str(exc))
            yield f"data: {err.model_dump_json(by_alias=True)}\n\n"
        except Exception as exc:
            logger.error("Unexpected error on /stream: %s", exc, exc_info=True)
            err = StreamChunk(event="error", session_id=request.session_id, sequence=-1, error_message="Internal server error")
            yield f"data: {err.model_dump_json(by_alias=True)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

__all__ = ["router"]
