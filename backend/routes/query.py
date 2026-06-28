"""
routes/query.py

FastAPI router for retrieval and generation endpoints.

Endpoints:
  POST /api/v1/query   — Standard non-streaming RAG query
  POST /api/v1/stream  — Streaming RAG query (Server-Sent Events)

Uses the ``RAGPipeline`` facade to execute the pipeline.
"""

from __future__ import annotations

import logging
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.models import QueryRequest, ChatResponse, ErrorResponse, StreamChunk
from services.rag_pipeline import RAGPipeline
from security.input_guard import SecurityError
from retrieval.filters import RetrievalError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["query"])

# Dependency to get pipeline instance
def get_pipeline() -> RAGPipeline:
    return RAGPipeline()


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
    pipeline: RAGPipeline = Depends(get_pipeline),
) -> ChatResponse:
    """
    Execute the full RAG pipeline and return a complete ``ChatResponse``.
    """
    logger.info("Received /query request for session %s", request.session_id)
    try:
        # Pipeline execution (non-async wrapper since pipeline is synchronous)
        # Note: in a fully async app, we would use run_in_threadpool here,
        # but the spec asks for simple straightforward integration.
        return pipeline.run(request)
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
    pipeline: RAGPipeline = Depends(get_pipeline),
) -> StreamingResponse:
    """
    Execute the full RAG pipeline with streaming LLM output.

    Returns a Server-Sent Events (SSE) stream of ``StreamChunk`` JSON strings.
    """
    logger.info("Received /stream request for session %s", request.session_id)

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            async for chunk in pipeline.stream(request):
                # SSE format: data: <json>\n\n
                yield f"data: {chunk.model_dump_json(by_alias=True)}\n\n"
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
