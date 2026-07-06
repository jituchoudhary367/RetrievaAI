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


async def _persist_message(user_id: str, session_id: str, role: str, content: str) -> None:
    """Dual-write chat history to Postgres (fire-and-forget), one message at a time."""
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
                if role == "user":
                    title = content[:50] + "..." if len(content) > 50 else content
                else:
                    title = "New Conversation"
                conv = Conversation(
                    session_id=session_id,
                    user_id=user_id,
                    title=title,
                )
                db.add(conv)
                await db.flush()
            
            conv.updated_at = datetime.utcnow()
            
            db.add(ConversationMessage(
                user_id=user_id,
                conversation_id=conv.id,
                role=role,
                content=content
            ))
            
            await db.commit()
    except Exception as e:
        logger.warning(f"Failed to persist {role} message to DB: {e}")


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
    
    try:
        from services.user_preferences import get_user_preferences
        from app.config import get_settings
        import os, dotenv
        prefs_svc = get_user_preferences()
        user_prefs = await prefs_svc.get_all_for_user(current_user.id)
        
        user_api_keys = {
            "GROQ_API_KEY": user_prefs.get("GROQ_API_KEY"),
        }
        
        if current_user.email == "jituchoudharyat@gmail.com":
            app_settings = get_settings()
            env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
            groq = dotenv.get_key(env_path, "GROQ_API_KEY") if os.path.exists(env_path) else getattr(app_settings, "groq_api_key", None)
            if not user_api_keys["GROQ_API_KEY"] and groq:
                user_api_keys["GROQ_API_KEY"] = groq
                
        if not user_api_keys.get("GROQ_API_KEY"):
            raise HTTPException(status_code=400, detail="GROQ_API_KEY is not configured in your integrations settings.")
            
        # Dual-write user message to Postgres instantly
        asyncio.create_task(_persist_message(
            user_id=current_user.id,
            session_id=request.session_id,
            role="user",
            content=request.query
        ))
            
        response = await pipeline.run(request, user_id=current_user.id, user_api_keys=user_api_keys)
        
        # Dual-write assistant response to Postgres
        asyncio.create_task(_persist_message(
            user_id=current_user.id,
            session_id=request.session_id,
            role="assistant",
            content=response.answer
        ))
        
        # Fire and forget telemetry
        asyncio.create_task(record_query_event(
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

    # Dual-write user message to Postgres instantly
    asyncio.create_task(_persist_message(
        user_id=current_user.id,
        session_id=request.session_id,
        role="user",
        content=request.query
    ))

    async def event_generator() -> AsyncGenerator[str, None]:
        from services.user_preferences import get_user_preferences
        from app.config import get_settings
        import os, dotenv
        prefs_svc = get_user_preferences()
        user_prefs = await prefs_svc.get_all_for_user(current_user.id)
        
        user_api_keys = {
            "GROQ_API_KEY": user_prefs.get("GROQ_API_KEY"),
        }
        
        if current_user.email == "jituchoudharyat@gmail.com":
            app_settings = get_settings()
            env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
            groq = dotenv.get_key(env_path, "GROQ_API_KEY") if os.path.exists(env_path) else getattr(app_settings, "groq_api_key", None)
            if not user_api_keys["GROQ_API_KEY"] and groq:
                user_api_keys["GROQ_API_KEY"] = groq
                from services.user_preferences import get_user_preferences
                asyncio.create_task(get_user_preferences().set(current_user.id, "GROQ_API_KEY", groq))
                
        if not user_api_keys.get("GROQ_API_KEY"):
            err = StreamChunk(event="error", session_id=request.session_id, sequence=0, error_message="GROQ_API_KEY is not configured in your integrations settings.")
            yield f"data: {err.model_dump_json(by_alias=True)}\n\n"
            return
            
        full_response_text = ""
        metadata_chunk = None
        citations = []
        
        try:
            async for chunk in pipeline.stream(request, user_id=current_user.id, user_api_keys=user_api_keys):
                # Accumulate the response to persist after stream completes
                if chunk.event == "token":
                    full_response_text += chunk.delta or ""
                elif chunk.event == "end":
                    metadata_chunk = chunk
                elif chunk.event == "citation":
                    citations.append(chunk.citation)

                # SSE format: data: <json>\n\n
                yield f"data: {chunk.model_dump_json(by_alias=True)}\n\n"
                
            # Stream completed successfully. Fire off persistence and telemetry.
            asyncio.create_task(_persist_message(
                user_id=current_user.id,
                session_id=request.session_id,
                role="assistant",
                content=full_response_text
            ))
            
            if metadata_chunk and metadata_chunk.metadata:
                m = metadata_chunk.metadata
                tu = m.token_usage
                asyncio.create_task(record_query_event(
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
            err = StreamChunk(event="error", session_id=request.session_id, sequence=0, error_message=str(exc))
            yield f"data: {err.model_dump_json(by_alias=True)}\n\n"
        except RetrievalError as exc:
            logger.warning("RetrievalError on /stream: %s", exc)
            err = StreamChunk(event="error", session_id=request.session_id, sequence=0, error_message=str(exc))
            yield f"data: {err.model_dump_json(by_alias=True)}\n\n"
        except Exception as exc:
            logger.error("Unexpected error on /stream: %s", exc, exc_info=True)
            err = StreamChunk(event="error", session_id=request.session_id, sequence=0, error_message="Internal server error")
            yield f"data: {err.model_dump_json(by_alias=True)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/suggest-questions")
async def get_suggested_questions(current_user: User = Depends(get_current_user)) -> list[str]:
    try:
        from db.models.document import Document
        from sqlalchemy import select
        async with async_session_factory() as db:
            result = await db.execute(
                select(Document.title)
                .where(Document.user_id == current_user.id)
                .order_by(Document.uploaded_at.desc())
                .limit(3)
            )
            docs = [d for d in result.scalars().all() if d]
            
        if not docs:
            return [
                "How does hybrid search work?",
                "What is CRAG?",
                "How is reranking done?",
                "Show me chunking strategies"
            ]
            
        questions = [
            f"What is the main topic of '{docs[0]}'?",
            f"Summarize the key points in '{docs[0]}'",
        ]
        if len(docs) > 1:
            questions.append(f"How do '{docs[0]}' and '{docs[1]}' compare?")
        else:
            questions.append(f"Are there any action items mentioned in '{docs[0]}'?")
            
        questions.append("Can you extract the most important entities from my documents?")
        return questions[:4]
    except Exception as exc:
        logger.error(f"Failed to get suggested questions: {exc}")
        return [
            "How does hybrid search work?",
            "What is CRAG?",
            "How is reranking done?",
            "Show me chunking strategies"
        ]

__all__ = ["router"]
