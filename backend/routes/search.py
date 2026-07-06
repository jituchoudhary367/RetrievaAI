"""
routes/search.py

Search endpoints (§1.1):
  POST /api/search (vector/hybrid document search)
  POST /api/search/web (Tavily external search)
  POST /api/search/code (GitHub external search)
  POST /api/search/events/click (telemetry)
"""

import asyncio
import time
from typing import List

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from app.models import SearchRequest, SearchResponse, SearchResult
from retrieval.hybrid_retriever import HybridRetriever
from retrieval.reranker import Reranker
from pipeline.embedder import Embedder
from pipeline.indexer import QdrantIndexer
from security.auth import get_current_user
from db.models.user import User
from db.models.user import User
from services.telemetry import record_search_event, record_search_click
from services.realtime_search import RealtimeSearchService
from tools.code_search import CodeSearchTool

router = APIRouter(tags=["Search"])

def get_hybrid_retriever() -> HybridRetriever:
    embedder = Embedder()
    qdrant = QdrantIndexer()
    return HybridRetriever(embedder=embedder, qdrant_indexer=qdrant)

def get_reranker() -> Reranker:
    return Reranker()

@router.post("/search", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
    retriever: HybridRetriever = Depends(get_hybrid_retriever),
    reranker: Reranker = Depends(get_reranker)
) -> SearchResponse:
    start_time = time.perf_counter()
    


    chunks = retriever.retrieve(
        query=request.query,
        user_id=current_user.id,
        top_k=request.top_k,
        filters=request.filters
    )
    
    if request.rerank and chunks:
        chunks = reranker.rerank(
            query=request.query, 
            chunks=chunks, 
            top_k=request.top_k
        )
        
    results: List[SearchResult] = []
    for chunk in chunks:
        score = chunk.rerank_score
        if score is None:
            score = chunk.fused_score
        if score is None:
            score = chunk.dense_score or chunk.sparse_score or 0.0
            
        results.append(
            SearchResult(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                text=chunk.text,
                score=score,
                source=chunk.source,
                metadata=chunk.metadata
            )
        )
        
    latency_ms = (time.perf_counter() - start_time) * 1000.0
    
    # ── Telemetry Fire & Forget ──
    # We await record_search_event to get the event ID, which is returned to the client 
    # so they can submit click events against it.
    event_id = await record_search_event(
        user_id=current_user.id,
        query_text=request.query,
        result_count=len(results),
        latency_ms=latency_ms
    )
    
    response = SearchResponse(
        query=request.query,
        results=results,
        total_results=len(results),
        latency_ms=latency_ms,
        debug_info={"raw_retrieved_count": len(chunks), "search_event_id": event_id} if request.include_debug_info else {"search_event_id": event_id}
    )
    # Inject search_event_id into debug_info so the frontend can retrieve it.
    if not response.debug_info:
        response.debug_info = {}
    response.debug_info["search_event_id"] = event_id
    
    return response


# ── Web Search ──
class WebSearchRequest(BaseModel):
    query: str
    max_results: int = 5

class WebSearchResponse(BaseModel):
    results: List[dict]
    latency_ms: float

@router.post("/search/web", response_model=WebSearchResponse)
async def search_web(
    request: WebSearchRequest,
    current_user: User = Depends(get_current_user),
) -> WebSearchResponse:
    start_time = time.perf_counter()
    service = RealtimeSearchService()
    # service.search returns List[RetrievedChunk]. We only need a few top results.
    service.max_results = request.max_results
    chunks = service.search(query=request.query)
    
    tool_results = []
    for c in chunks:
        tool_results.append({
            "title": c.metadata.get("title", ""),
            "url": c.metadata.get("url", ""),
            "snippet": c.text
        })
        
    latency_ms = (time.perf_counter() - start_time) * 1000.0
    
    return WebSearchResponse(
        results=tool_results,
        latency_ms=latency_ms
    )


# ── Code Search ──
class CodeSearchRequest(BaseModel):
    query: str
    repo: str
    max_results: int = 5

class CodeSearchResponse(BaseModel):
    results: List[dict]
    latency_ms: float

@router.post("/search/code", response_model=CodeSearchResponse)
async def search_code(
    request: CodeSearchRequest,
    current_user: User = Depends(get_current_user),
) -> CodeSearchResponse:
    start_time = time.perf_counter()
    tool = CodeSearchTool()
    tool_results = tool.execute(query=request.query, repo=request.repo, max_results=request.max_results)
    latency_ms = (time.perf_counter() - start_time) * 1000.0
    
    return CodeSearchResponse(
        results=tool_results,
        latency_ms=latency_ms
    )


# ── Click Telemetry ──
class SearchClickRequest(BaseModel):
    search_event_id: str
    chunk_id: str

@router.post("/search/events/click", status_code=200)
async def search_click_event(
    request: SearchClickRequest,
    current_user: User = Depends(get_current_user),
) -> None:
    # Fire and forget
    asyncio.create_task(record_search_click(
        user_id=current_user.id,
        search_event_id=request.search_event_id,
        chunk_id=request.chunk_id
    ))
