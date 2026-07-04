"""
services/rag_pipeline.py

Master RAG pipeline orchestrator.

Pipeline order (per Milestone 3 spec):
  1. InputGuard.validate
  2. SemanticCache.get  (return early on hit when use_cache=True)
  3. ConversationStore.get_history
  4. QueryRouter.route
  5. QueryDecomposer.decompose
  6. HybridRetriever.retrieve  (per sub-query, results merged)
  7. Reranker.rerank
  8. CragAgent.correct  (when features.enable_crag is True)
  9. Context builder (rank + format retrieved chunks)
  10. LLM generation (streaming or non-streaming)
  11. OutputGuard.verify
  12. ConversationStore.add_message  (save history)
  13. SemanticCache.set  (populate cache when use_cache=True)
  14. Return ChatResponse

Public methods (exact signatures matched by routes/query.py):
  run(request: QueryRequest) -> ChatResponse
  stream(request: QueryRequest) -> AsyncIterator[StreamChunk]
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import AsyncIterator, List, Optional

from services.conversation import ConversationStore
from services.query_router import QueryRouter
from services.query_decomposer import QueryDecomposer
from retrieval.hybrid_retriever import HybridRetriever
from retrieval.reranker import Reranker
from services.document_grader import DocumentGrader
from agents.crag import CragAgent
from services.semantic_cache import SemanticCache
from security.input_guard import InputGuard, SecurityError
from services.runtime_settings import get_runtime_settings
from security.output_guard import OutputGuard
from prompts import render_rag_prompt, render_system_prompt
from app.config import LLMSettings, get_settings
from app.models import (
    QueryRequest,
    ChatResponse,
    StreamChunk,
    Citation,
    ResponseMetadata,
    TokenUsage,
    RetrievedChunk,
    ChatMessage,
    MessageRole,
    StreamEventType,
    QueryIntent,
)

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    Orchestrates the full RAG pipeline from request validation to response.

    Parameters
    ----------
    All parameters are optional and default to fresh instances.  Pass
    pre-built instances for testing or resource sharing.
    """

    def __init__(
        self,
        conversation_store: Optional[ConversationStore] = None,
        query_router: Optional[QueryRouter] = None,
        query_decomposer: Optional[QueryDecomposer] = None,
        retriever: Optional[HybridRetriever] = None,
        reranker: Optional[Reranker] = None,
        document_grader: Optional[DocumentGrader] = None,
        crag_agent: Optional[CragAgent] = None,
        semantic_cache: Optional[SemanticCache] = None,
        input_guard: Optional[InputGuard] = None,
        output_guard: Optional[OutputGuard] = None,
    ) -> None:
        self._store = conversation_store or ConversationStore()
        self._router = query_router or QueryRouter()
        self._decomposer = query_decomposer or QueryDecomposer()
        self._retriever = retriever or HybridRetriever()
        self._reranker = reranker or Reranker()
        self._grader = document_grader or DocumentGrader()
        self._crag = crag_agent or CragAgent()
        self._cache = semantic_cache or SemanticCache()
        self._input_guard = input_guard or InputGuard()
        self._output_guard = output_guard or OutputGuard()

        from tools.web_search import WebSearchTool
        self._web_search = WebSearchTool()

    # ------------------------------------------------------------------
    # Non-streaming
    # ------------------------------------------------------------------

    async def run(self, request: QueryRequest, user_id: str, user_api_keys: dict = None) -> ChatResponse:
        """
        Execute the full RAG pipeline and return a ``ChatResponse``.

        This is the primary non-streaming path called by ``routes/query.py``.
        """
        t_start = time.monotonic()

        # 1. Input validation
        try:
            await self._input_guard.validate(request)
        except SecurityError as exc:
            raise  # Let the route handler convert to ErrorResponse

        # 1.5 Fetch keys
        cfg = get_settings()
        user_api_keys = user_api_keys or {}
        llm_api_key = user_api_keys.get("GROQ_API_KEY") or cfg.resolved_llm_api_key()
        embed_api_key = cfg.resolved_embedding_api_key()
        if user_api_keys.get("SERPER_API_KEY"):
            self._web_search._serper_key = user_api_keys["SERPER_API_KEY"]
        
        # Override embedder settings for this request
        self._retriever._embedder._cfg = self._retriever._embedder._cfg.model_copy(update={"api_key": embed_api_key})

        # 2. Semantic cache lookup
        if request.use_cache:
            cached = self._cache.get(request.query, user_id=user_id)
            if cached is not None:
                cached.metadata.used_cache = True
                return cached

        # 3. Conversation history
        history = self._store.get_history(request.session_id, user_id=user_id)

        # 4. Query routing
        intent = self._router.route(request.query, history=history)

        # 5. Query decomposition
        sub_queries = self._decomposer.decompose(request.query)

        # 6. Retrieval (merge results from all sub-queries)
        t_retrieval_start = time.monotonic()
        all_chunks: List[RetrievedChunk] = []
        used_web_search = False

        if request.force_web_search:
            try:
                from app.models import RetrievalSource
                web_results = self._web_search.search(request.query, top_k=3)
                for res in web_results:
                    snippet = res.get("snippet", "").strip()
                    if snippet:
                        all_chunks.append(
                            RetrievedChunk(
                                chunk_id=f"web:{hash(snippet) & 0xFFFFFFFF:08x}",
                                document_id=res.get("url", "web"),
                                text=snippet,
                                source=RetrievalSource.WEB,
                                metadata={
                                    "title": res.get("title", ""),
                                    "url": res.get("url", ""),
                                    "source_type": "web",
                                },
                            )
                        )
                used_web_search = True
            except Exception as e:
                logger.warning(f"Web search failed in pipeline: {e}")
                
        # Always do document retrieval
        for sq in sub_queries:
            chunks = self._retriever.retrieve(
                query=sq,
                user_id=user_id,
                top_k=request.top_k,
                filters=request.filters or [],
            )
            all_chunks.extend(chunks)

        seen_ids: set = set()
        unique_chunks: List[RetrievedChunk] = []
        for c in all_chunks:
            if c.chunk_id not in seen_ids:
                seen_ids.add(c.chunk_id)
                unique_chunks.append(c)

        retrieval_latency = (time.monotonic() - t_retrieval_start) * 1000

        # 7. Rerank
        reranked = self._reranker.rerank(request.query, unique_chunks, top_n=request.top_k)

        # 8. CRAG correction
        settings = get_settings()
        if settings.features.enable_crag:
            reranked = self._crag.correct(request.query, reranked)

        # 9. Context builder
        context_str, citations = self._build_context(reranked)

        # 10. LLM generation
        t_gen_start = time.monotonic()
        answer, token_usage = self._generate(
            query=request.query,
            context=context_str,
            history=history,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            api_key=llm_api_key,
        )
        generation_latency = (time.monotonic() - t_gen_start) * 1000

        # 11. Output guard
        guard_result = self._output_guard.verify(answer, citations)
        if not guard_result.is_valid:
            logger.warning(
                "OutputGuard flagged response: %s", guard_result.warnings
            )

        total_latency = (time.monotonic() - t_start) * 1000

        metadata = ResponseMetadata(
            intent=intent,
            used_cache=False,
            used_web_search=used_web_search,
            retrieval_latency_ms=retrieval_latency,
            generation_latency_ms=generation_latency,
            total_latency_ms=total_latency,
            token_usage=token_usage,
            model_name=settings.llm.model_name,
            retrieved_count=len(all_chunks),
            reranked_count=len(reranked),
            top_k=request.top_k,
        )

        response = ChatResponse(
            session_id=request.session_id,
            answer=answer,
            citations=citations,
            metadata=metadata,
        )

        # 12. Save conversation history
        self._store.add_message(
            request.session_id,
            ChatMessage(role=MessageRole.USER, content=request.query),
            user_id=user_id
        )
        self._store.add_message(
            request.session_id,
            ChatMessage(role=MessageRole.ASSISTANT, content=answer),
            user_id=user_id
        )
        self._store.summarize_if_needed(request.session_id, user_id=user_id)

        # 13. Populate cache
        if request.use_cache:
            self._cache.set(request.query, response, user_id=user_id)

        return response

    # ------------------------------------------------------------------
    # Streaming
    # ------------------------------------------------------------------

    async def stream(self, request: QueryRequest, user_id: str, user_api_keys: dict = None) -> AsyncIterator[StreamChunk]:
        """
        Execute the pipeline with streaming LLM generation.

        Yields ``StreamChunk`` objects:
          START   → pipeline begin
          TOKEN   → each LLM text token
          CITATION → each citation after generation
          END     → pipeline complete with metadata
        """
        t_start = time.monotonic()
        seq = 0

        # 1. Input validation
        try:
            await self._input_guard.validate(request)
        except SecurityError as exc:
            yield StreamChunk(
                event=StreamEventType.ERROR,
                session_id=request.session_id,
                sequence=seq,
                error_message=str(exc),
            )
            return

        yield StreamChunk(
            event=StreamEventType.START,
            session_id=request.session_id,
            sequence=seq,
        )
        seq += 1
        # 1.5 Fetch keys
        cfg = get_settings()
        user_api_keys = user_api_keys or {}
        llm_api_key = user_api_keys.get("GROQ_API_KEY") or cfg.resolved_llm_api_key()
        embed_api_key = cfg.resolved_embedding_api_key()
        if user_api_keys.get("SERPER_API_KEY"):
            self._web_search._serper_key = user_api_keys["SERPER_API_KEY"]
        
        # Override embedder settings for this request
        self._retriever._embedder._cfg = self._retriever._embedder._cfg.model_copy(update={"api_key": embed_api_key})

        # 2. Cache
        if request.use_cache:
            cached = self._cache.get(request.query, user_id=user_id)
            if cached is not None:
                async for chunk in self._replay_cached(cached, request.session_id, seq):
                    yield chunk
                return

        # 3–9. Same as non-streaming (retrieval is not streamed)
        history = self._store.get_history(request.session_id, user_id=user_id)
        intent = self._router.route(request.query, history=history)
        sub_queries = self._decomposer.decompose(request.query)

        all_chunks: List[RetrievedChunk] = []
        used_web_search = False

        if request.force_web_search:
            try:
                from app.models import RetrievalSource
                web_results = self._web_search.search(request.query, top_k=3)
                for res in web_results:
                    snippet = res.get("snippet", "").strip()
                    if snippet:
                        all_chunks.append(
                            RetrievedChunk(
                                chunk_id=f"web:{hash(snippet) & 0xFFFFFFFF:08x}",
                                document_id=res.get("url", "web"),
                                text=snippet,
                                source=RetrievalSource.WEB,
                                metadata={
                                    "title": res.get("title", ""),
                                    "url": res.get("url", ""),
                                    "source_type": "web",
                                },
                            )
                        )
                used_web_search = True
            except Exception as e:
                logger.warning(f"Web search failed in pipeline: {e}")
                
        # Always do document retrieval
        for sq in sub_queries:
            all_chunks.extend(
                self._retriever.retrieve(query=sq, user_id=user_id, top_k=request.top_k, filters=request.filters or [])
            )

        seen_ids: set = set()
        unique_chunks: List[RetrievedChunk] = []
        for c in all_chunks:
            if c.chunk_id not in seen_ids:
                seen_ids.add(c.chunk_id)
                unique_chunks.append(c)

        settings = get_settings()
        reranked = self._reranker.rerank(request.query, unique_chunks, top_n=request.top_k)
                    
        if settings.features.enable_crag:
            reranked = self._crag.correct(request.query, reranked)

        context_str, citations = self._build_context(reranked)

        # 10. Stream LLM tokens
        full_answer = ""
        token_usage: Optional[TokenUsage] = None

        async for token in self._stream_llm(
            query=request.query,
            context=context_str,
            history=history,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            api_key=llm_api_key,
        ):
            full_answer += token
            yield StreamChunk(
                event=StreamEventType.TOKEN,
                session_id=request.session_id,
                sequence=seq,
                delta=token,
            )
            seq += 1

        # Emit citations
        for cit in citations:
            yield StreamChunk(
                event=StreamEventType.CITATION,
                session_id=request.session_id,
                sequence=seq,
                citation=cit,
            )
            seq += 1

        total_latency = (time.monotonic() - t_start) * 1000
        meta = ResponseMetadata(
            intent=intent,
            used_cache=False,
            used_web_search=used_web_search,
            total_latency_ms=total_latency,
            model_name=settings.llm.model_name,
            retrieved_count=len(all_chunks),
            reranked_count=len(reranked),
            top_k=request.top_k,
        )

        yield StreamChunk(
            event=StreamEventType.END,
            session_id=request.session_id,
            sequence=seq,
            metadata=meta,
        )

        # 12. Save history
        self._store.add_message(request.session_id, ChatMessage(role=MessageRole.USER, content=request.query), user_id=user_id)
        self._store.add_message(request.session_id, ChatMessage(role=MessageRole.ASSISTANT, content=full_answer), user_id=user_id)
        self._store.summarize_if_needed(request.session_id, user_id=user_id)

        # 13. Cache
        if request.use_cache and full_answer:
            response = ChatResponse(
                session_id=request.session_id,
                answer=full_answer,
                citations=citations,
                metadata=meta,
            )
            self._cache.set(request.query, response, user_id=user_id)

    # ------------------------------------------------------------------
    # Context building
    # ------------------------------------------------------------------

    def _build_context(
        self, chunks: List[RetrievedChunk]
    ) -> tuple[str, List[Citation]]:
        """Format retrieved chunks into a context string and citation list."""
        parts: List[str] = []
        citations: List[Citation] = []

        for i, chunk in enumerate(chunks, start=1):
            parts.append(
                f"[{i}] (chunk_id={chunk.chunk_id})\n{chunk.text}"
            )
            citations.append(
                Citation(
                    document_id=chunk.document_id,
                    chunk_id=chunk.chunk_id,
                    source=chunk.metadata.get("source_path", chunk.document_id),
                    text_snippet=chunk.text[:500],
                    score=min(1.0, max(0.0, chunk.rerank_score or chunk.fused_score or chunk.dense_score or 0.5)),
                    url=chunk.metadata.get("url"),
                )
            )

        return "\n\n---\n\n".join(parts), citations

    # ------------------------------------------------------------------
    # LLM generation
    # ------------------------------------------------------------------

    def _generate(
        self,
        query: str,
        context: str,
        history: List[ChatMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        api_key: Optional[str] = None,
    ) -> tuple[str, Optional[TokenUsage]]:
        cfg = get_settings()
        temp = temperature if temperature is not None else cfg.llm.temperature
        tokens = max_tokens if max_tokens is not None else cfg.llm.max_tokens
        provider = cfg.llm.provider.value
        resolved_key = api_key or cfg.resolved_llm_api_key()
        system_prompt = render_system_prompt()
        user_prompt = render_rag_prompt(query, context)

        messages = self._build_messages(history, user_prompt)

        if provider == "anthropic":
            return self._generate_anthropic(
                system_prompt, messages, temp, tokens, cfg.llm.model_name, resolved_key
            )
        if provider in ("openai", "groq", "openrouter"):
            return self._generate_openai(
                system_prompt, messages, temp, tokens, cfg.llm.model_name, resolved_key, cfg.resolved_llm_base_url()
            )
        if provider == "ollama":
            return self._generate_ollama(
                system_prompt, messages, temp, tokens, cfg.llm.model_name
            )

        logger.warning("Unsupported LLM provider %s; returning empty answer.", provider)
        return "", None

    def _generate_anthropic(
        self, system: str, messages: list, temp: float, max_tok: int,
        model: str, api_key: Optional[str]
    ) -> tuple[str, Optional[TokenUsage]]:
        import anthropic  # noqa: PLC0415
        client = anthropic.Anthropic(api_key=api_key)
        resp = client.messages.create(
            model=model,
            system=system,
            messages=messages,
            temperature=temp,
            max_tokens=max_tok,
        )
        answer = resp.content[0].text if resp.content else ""
        usage = TokenUsage(
            prompt_tokens=resp.usage.input_tokens,
            completion_tokens=resp.usage.output_tokens,
        )
        return answer, usage

    def _generate_openai(
        self, system: str, messages: list, temp: float, max_tok: int,
        model: str, api_key: Optional[str], base_url: Optional[str] = None
    ) -> tuple[str, Optional[TokenUsage]]:
        import openai  # noqa: PLC0415
        full_messages = [{"role": "system", "content": system}] + messages
        oc = openai.OpenAI(api_key=api_key, base_url=base_url)
        resp = oc.chat.completions.create(
            model=model,
            messages=full_messages,
            temperature=temp,
            max_tokens=max_tok,
        )
        answer = resp.choices[0].message.content or ""
        usage = TokenUsage(
            prompt_tokens=resp.usage.prompt_tokens,
            completion_tokens=resp.usage.completion_tokens,
        ) if resp.usage else None
        return answer, usage

    def _generate_ollama(
        self, system: str, messages: list, temp: float, max_tok: int, model: str
    ) -> tuple[str, Optional[TokenUsage]]:
        try:
            import httpx  # noqa: PLC0415
            full_messages = [{"role": "system", "content": system}] + messages
            with httpx.Client(timeout=60) as client:
                resp = client.post(
                    "http://localhost:11434/api/chat",
                    json={"model": model, "messages": full_messages, "stream": False},
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("message", {}).get("content", ""), None
        except Exception as exc:
            logger.error("Ollama generation failed: %s", exc)
            return "", None

    async def _stream_llm(
        self,
        query: str,
        context: str,
        history: List[ChatMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        api_key: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """Yield text tokens from the LLM."""
        cfg = get_settings()
        temp = temperature if temperature is not None else cfg.llm.temperature
        tokens = max_tokens if max_tokens is not None else cfg.llm.max_tokens
        provider = cfg.llm.provider.value
        resolved_key = api_key or cfg.resolved_llm_api_key()
        system_prompt = render_system_prompt()
        user_prompt = render_rag_prompt(query, context)
        messages = self._build_messages(history, user_prompt)

        if provider == "anthropic":
            async for token in self._stream_anthropic(
                system_prompt, messages, temp, tokens, cfg.llm.model_name, resolved_key
            ):
                yield token
        elif provider in ("openai", "groq", "openrouter"):
            async for token in self._stream_openai(
                system_prompt, messages, temp, tokens, cfg.llm.model_name, resolved_key, cfg.resolved_llm_base_url()
            ):
                yield token
        else:
            # Fallback: non-streaming call, emit as one chunk
            answer, _ = self._generate(query, context, history, temperature, max_tokens, api_key=resolved_key)
            if answer:
                yield answer

    async def _stream_anthropic(
        self, system: str, messages: list, temp: float, max_tok: int,
        model: str, api_key: Optional[str]
    ) -> AsyncIterator[str]:
        import anthropic  # noqa: PLC0415
        client = anthropic.Anthropic(api_key=api_key)
        with client.messages.stream(
            model=model,
            system=system,
            messages=messages,
            temperature=temp,
            max_tokens=max_tok,
        ) as stream:
            for text in stream.text_stream:
                yield text
                await asyncio.sleep(0)

    async def _stream_openai(
        self, system: str, messages: list, temp: float, max_tok: int,
        model: str, api_key: Optional[str], base_url: Optional[str] = None
    ) -> AsyncIterator[str]:
        import openai  # noqa: PLC0415
        full_messages = [{"role": "system", "content": system}] + messages
        oc = openai.OpenAI(api_key=api_key, base_url=base_url)
        with oc.chat.completions.create(
            model=model,
            messages=full_messages,
            temperature=temp,
            max_tokens=max_tok,
            stream=True,
        ) as stream:
            for chunk in stream:
                delta = chunk.choices[0].delta.content if chunk.choices else None
                if delta:
                    yield delta
                    await asyncio.sleep(0)

    async def _replay_cached(
        self, cached: ChatResponse, session_id: str, seq: int
    ) -> AsyncIterator[StreamChunk]:
        """Emit a cached response as a stream."""
        words = cached.answer.split()
        for word in words:
            yield StreamChunk(
                event=StreamEventType.TOKEN,
                session_id=session_id,
                sequence=seq,
                delta=word + " ",
            )
            seq += 1
        for cit in cached.citations:
            yield StreamChunk(
                event=StreamEventType.CITATION,
                session_id=session_id,
                sequence=seq,
                citation=cit,
            )
            seq += 1
        meta = ResponseMetadata(used_cache=True)
        yield StreamChunk(
            event=StreamEventType.END,
            session_id=session_id,
            sequence=seq,
            metadata=meta,
        )

    @staticmethod
    def _build_messages(history: List[ChatMessage], user_prompt: str) -> list:
        """Convert ChatMessage history + current user prompt to provider format."""
        messages = []
        for msg in history[-6:]:  # last 3 turns
            messages.append({
                "role": msg.role.value,
                "content": msg.content,
            })
        messages.append({"role": "user", "content": user_prompt})
        return messages


__all__ = ["RAGPipeline"]
