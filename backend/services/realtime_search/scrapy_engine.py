import logging
from typing import Dict, Optional
import httpx
from scrapy.selector import Selector
from .cleaner import normalize_document

logger = logging.getLogger(__name__)

class ScrapyEngine:
    """Fallback engine using httpx and scrapy.Selector."""
    def __init__(self, timeout: float = 15.0):
        self.timeout = timeout
        
    def fetch_and_parse(self, url: str) -> Optional[Dict[str, str]]:
        logger.info(f"Switching To Scrapy for {url}")
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                response = client.get(url)
                response.raise_for_status()
                
            selector = Selector(text=response.text)
            
            # Remove scripts, styles, navs
            for bad_tag in selector.xpath('//script | //style | //nav | //footer | //header | //aside'):
                bad_tag.root.getparent().remove(bad_tag.root)
                
            title = selector.css('title::text').get(default=url)
            
            # Get remaining text
            texts = selector.xpath('//body//text()').getall()
            content = " ".join(t.strip() for t in texts if t.strip())
            
            if not content or len(content) < 50:
                logger.warning(f"Scrapy Failed: Not enough content on {url}")
                return None
                
            doc = {
                "title": title,
                "url": url,
                "content": content
            }
            logger.info(f"Scrapy Success for {url}")
            return normalize_document(doc)
            
        except Exception as e:
            logger.warning(f"Scrapy Failed for {url}: {e}")
            return None
