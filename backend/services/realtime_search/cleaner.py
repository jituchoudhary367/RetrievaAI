import re
from typing import Dict

def clean_html_text(text: str) -> str:
    # Remove multiple spaces and newlines
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r' +', ' ', text)
    return text.strip()

def normalize_document(doc: Dict[str, str]) -> Dict[str, str]:
    """Ensure the document has required fields and normalized text."""
    return {
        "title": clean_html_text(doc.get("title", "")),
        "url": doc.get("url", ""),
        "content": clean_html_text(doc.get("content", "")),
    }
