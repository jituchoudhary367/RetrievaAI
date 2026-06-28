import time
from fastapi import APIRouter, Depends
from typing import List

from app.models import SearchRequest, SearchResponse, SearchResult
from retrieval.hybrid_retriever import HybridRetriever
from retrieval.reranker import Reranker
from pipeline.embedder import Embedder
from pipeline.indexer import QdrantIndexer, BM25Index

router = APIRouter(tags=["Search"])

def get_hybrid_retriever() -> HybridRetriever:
    embedder = Embedder()
    qdrant = QdrantIndexer()
    bm25 = BM25Index()
    return HybridRetriever(embedder=embedder, qdrant_indexer=qdrant, bm25_index=bm25)

def get_reranker() -> Reranker:
    return Reranker()

@router.post("/search", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    retriever: HybridRetriever = Depends(get_hybrid_retriever),
    reranker: Reranker = Depends(get_reranker)
) -> SearchResponse:
    start_time = time.perf_counter()
    
    # Retrieve
    chunks = retriever.retrieve(
        query=request.query,
        top_k=request.top_k,
        filters=request.filters
    )
    
    # Rerank
    if request.rerank and chunks:
        chunks = reranker.rerank(
            query=request.query, 
            chunks=chunks, 
            top_k=request.top_k
        )
        
    # Map to SearchResult
    results: List[SearchResult] = []
    for chunk in chunks:
        # Use rerank score if available, fallback to fused or dense/sparse
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
    
    return SearchResponse(
        query=request.query,
        results=results,
        total_results=len(results),
        latency_ms=latency_ms,
        debug_info={"raw_retrieved_count": len(chunks)} if request.include_debug_info else None
    )
