from typing import List, Dict
import logging
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

class SearchProvider:
    def search(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        raise NotImplementedError

class DuckDuckGoProvider(SearchProvider):
    def search(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        logger.info(f"Generating Search Query: {query}")
        logger.info("Fetching Candidate URLs via DuckDuckGo")
        results = []
        try:
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", "")
                    })
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
        return results
