import logging
from typing import Dict, Optional
from scrapling import Fetcher
from .cleaner import normalize_document

logger = logging.getLogger(__name__)

class ScraplingEngine:
    """Primary engine using Scrapling to fetch and parse pages."""
    def __init__(self, timeout: float = 15.0):
        self.timeout = timeout
        
    def fetch_and_parse(self, url: str) -> Optional[Dict[str, str]]:
        logger.info(f"Scrapling Started for {url}")
        try:
            fetcher = Fetcher()
            # Suppress deprecation by not passing timeout directly to constructor if not supported
            try:
                fetcher.configure(timeout=self.timeout)
            except Exception:
                pass # ignore if configure doesn't exist
            page = fetcher.get(url)
            
            # Basic extraction, Scrapling handles most stealth and parsing
            # You can extract specific tags or just get text
            # Usually page.text gets the text content, let's just get the body text
            title = page.css("title::text").get(default=url)
            import trafilatura
            content = trafilatura.extract(page.html_content)
            if not content:
                # fallback to basic text extraction
                content = page.body.get_all_text() if page.body else ""
            
            if not content or len(content.strip()) < 50:
                logger.warning(f"Scrapling Failed: Not enough content on {url}")
                return None
                
            doc = {
                "title": title,
                "url": url,
                "content": content
            }
            logger.info(f"Scrapling Success for {url}")
            return normalize_document(doc)
            
        except Exception as e:
            logger.warning(f"Scrapling Failed for {url}: {e}")
            return None
