import logging
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.models import RetrievedChunk, RetrievalSource
from app.config import get_settings
from .search_provider import DuckDuckGoProvider
from .scrapling_engine import ScraplingEngine
from .scrapy_engine import ScrapyEngine

logger = logging.getLogger(__name__)

class RealtimeSearchService:
    """Orchestrates live web retrieval."""
    
    def __init__(self):
        cfg = get_settings().realtime_search
        self.provider = DuckDuckGoProvider()
        self.scrapling = ScraplingEngine(timeout=cfg.timeout_seconds)
        self.scrapy = ScrapyEngine(timeout=cfg.timeout_seconds)
        self.max_results = cfg.concurrent_fetches
        
    def search(self, query: str) -> List[RetrievedChunk]:
        cfg = get_settings().realtime_search
        if not cfg.enabled:
            logger.info("Realtime Search Disabled")
            logger.info("Skipping Internet Retrieval")
            return []
            
        logger.info(f"Generating Search Query: {query}")
        candidate_results = self.provider.search(query, max_results=self.max_results)
        
        if not candidate_results:
            logger.warning("No candidate URLs found.")
            return []
            
        chunks = []
        
        # We fetch concurrently
        with ThreadPoolExecutor(max_workers=self.max_results) as executor:
            future_to_url = {
                executor.submit(self._fetch_url, res["url"]): res 
                for res in candidate_results
            }
            
            for future in as_completed(future_to_url):
                res = future_to_url[future]
                try:
                    doc = future.result()
                    if doc:
                        snippet = doc["content"][:2000] # take up to 2k chars
                        if snippet:
                            chunks.append(
                                RetrievedChunk(
                                    chunk_id=f"web:{hash(snippet) & 0xFFFFFFFF:08x}",
                                    document_id=doc["url"],
                                    text=snippet,
                                    source=RetrievalSource.WEB,
                                    metadata={
                                        "title": doc.get("title", ""),
                                        "url": doc["url"],
                                        "source_type": "web"
                                    }
                                )
                            )
                except Exception as e:
                    logger.warning(f"Failed to process {res['url']}: {e}")
                    
        return chunks

    def _fetch_url(self, url: str) -> dict:
        # 1. Try Scrapling
        doc = self.scrapling.fetch_and_parse(url)
        if doc:
            return doc
            
        # 2. Fallback to Scrapy
        doc = self.scrapy.fetch_and_parse(url)
        return doc
