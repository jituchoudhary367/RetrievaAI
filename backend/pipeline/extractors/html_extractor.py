"""
pipeline/extractors/html_extractor.py

Extracts clean article text, tables, and rich metadata from HTML documents
and raw HTML strings.

Fits into the ingestion pipeline as the extractor registered for .html and
.htm files.  `pipeline/ingest.py` dispatches to this class via the standard
`BaseExtractor` interface; downstream pipeline stages receive only the
normalized `ExtractionResult`.

Dependency chain (all optional):
  beautifulsoup4  → DOM parsing and fallback boilerplate removal
  lxml            → fast HTML parser backend for BeautifulSoup
  trafilatura     → superior boilerplate stripping (preferred when installed)
"""

from __future__ import annotations

import html
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from pipeline.extractors.text_extractor import (
    BaseExtractor,
    DEFAULT_ENCODING_FALLBACKS,
    ExtractionError,
    ExtractionResult,
)
from app.models import DocumentMetadata

logger = logging.getLogger(__name__)

# Tags whose entire subtree we strip before extracting text
_NOISE_TAGS = frozenset(
    {
        "script",
        "style",
        "nav",
        "header",
        "footer",
        "aside",
        "form",
        "noscript",
        "iframe",
        "svg",
        "figure",
    }
)


class HtmlExtractor(BaseExtractor):
    """
    Extracts clean text, tables, and metadata from HTML files.

    Boilerplate-removal strategy:
    1. ``trafilatura`` (preferred) — state-of-the-art article extractor.
    2. Fallback: strip noise tags via BeautifulSoup then collect remaining
       paragraph/heading/list text.

    Both paths also extract ``<table>`` elements and a rich metadata set
    (title, description, og:* tags, canonical URL, language, author).
    """

    supported_extensions = frozenset({".html", ".htm"})

    def __init__(self, max_file_size_bytes: Optional[int] = None) -> None:
        from app.config import get_settings
        settings = get_settings()
        self.max_file_size_bytes = max_file_size_bytes or getattr(
            settings, "max_ingest_file_size_bytes", 150 * 1024 * 1024
        )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def extract(self, file_path: Path) -> ExtractionResult:
        self._validate_file(file_path, self.max_file_size_bytes)

        raw_bytes = file_path.read_bytes()
        html_str = self._decode(file_path.name, raw_bytes)

        try:
            return self._extract_from_html(html_str, file_path)
        except ExtractionError:
            raise
        except Exception as exc:
            logger.exception("Unexpected failure extracting HTML %s", file_path)
            raise ExtractionError(f"Failed to extract {file_path}: {exc}") from exc

    # ------------------------------------------------------------------
    # Core extraction
    # ------------------------------------------------------------------

    def _extract_from_html(
        self, html_str: str, file_path: Path
    ) -> ExtractionResult:
        warnings: List[str] = []

        # --- BeautifulSoup parse (required) ---
        try:
            from bs4 import BeautifulSoup  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "beautifulsoup4 is required for HTML extraction. "
                "Install it with: pip install beautifulsoup4 lxml"
            ) from exc

        try:
            parser = "lxml"
            import lxml  # noqa: F401, PLC0415
        except ImportError:
            parser = "html.parser"
            warnings.append(
                "lxml not installed — falling back to html.parser (slower). "
                "Install with: pip install lxml"
            )

        soup = BeautifulSoup(html_str, parser)

        # --- Metadata extraction ---
        metadata = self._build_metadata(file_path, soup)

        # --- Table extraction ---
        tables = self._extract_tables(soup)

        # --- Boilerplate removal ---
        # Remove noise tags from the soup copy used for text extraction
        for tag in _NOISE_TAGS:
            for element in soup.find_all(tag):
                element.decompose()

        text = self._extract_text(html_str, soup, warnings)

        if not text.strip():
            raise ExtractionError(f"No usable text extracted from {file_path}")

        return ExtractionResult(
            text=text,
            metadata=metadata,
            tables=tables,
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # Text extraction
    # ------------------------------------------------------------------

    def _extract_text(
        self, raw_html: str, stripped_soup: Any, warnings: List[str]
    ) -> str:
        """Try trafilatura first; fall back to BeautifulSoup heuristic."""
        try:
            import trafilatura  # noqa: PLC0415
            result = trafilatura.extract(
                raw_html,
                include_tables=False,
                include_links=False,
                include_images=False,
                no_fallback=False,
            )
            if result and len(result.strip()) > 50:
                return result
            warnings.append(
                "trafilatura returned little/no text — falling back to "
                "BeautifulSoup heuristic."
            )
        except ImportError:
            logger.debug(
                "trafilatura not installed; using BeautifulSoup heuristic. "
                "Install with: pip install trafilatura"
            )

        return self._bs4_text(stripped_soup)

    def _bs4_text(self, soup: Any) -> str:
        """Collect text from semantic content tags, preserving structure."""
        content_tags = [
            "article",
            "main",
            "section",
            "p",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "li",
            "td",
            "th",
            "blockquote",
            "pre",
            "code",
        ]
        parts: List[str] = []
        for tag in soup.find_all(content_tags):
            text = tag.get_text(separator=" ", strip=True)
            if text:
                parts.append(text)

        if not parts:
            # Last resort: get all visible text
            text = soup.get_text(separator="\n", strip=True)
            text = re.sub(r"\n{3,}", "\n\n", text)
            return text

        return "\n\n".join(parts)

    # ------------------------------------------------------------------
    # Table extraction
    # ------------------------------------------------------------------

    def _extract_tables(self, soup: Any) -> List[List[List[str]]]:
        all_tables: List[List[List[str]]] = []
        for table_tag in soup.find_all("table"):
            rows: List[List[str]] = []
            for row_tag in table_tag.find_all("tr"):
                cells = [
                    cell.get_text(separator=" ", strip=True)
                    for cell in row_tag.find_all(["td", "th"])
                ]
                if cells:
                    rows.append(cells)
            if rows:
                all_tables.append(rows)
        return all_tables

    # ------------------------------------------------------------------
    # Metadata extraction
    # ------------------------------------------------------------------

    def _build_metadata(self, file_path: Path, soup: Any) -> DocumentMetadata:
        base = self._base_metadata(file_path, "html")
        extra: Dict[str, Any] = dict(base.extra)

        # Title
        title: Optional[str] = None
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            title = og_title["content"].strip()
        elif soup.title and soup.title.string:
            title = soup.title.string.strip()

        # Description
        desc_tag = soup.find("meta", attrs={"name": "description"})
        og_desc = soup.find("meta", property="og:description")
        description = (
            (og_desc and og_desc.get("content"))
            or (desc_tag and desc_tag.get("content"))
            or None
        )
        if description:
            extra["description"] = str(description).strip()

        # Author
        author_tag = soup.find("meta", attrs={"name": "author"})
        author: Optional[str] = (
            str(author_tag["content"]).strip() if author_tag and author_tag.get("content") else None
        )

        # og:url / canonical
        og_url = soup.find("meta", property="og:url")
        canonical = soup.find("link", rel="canonical")
        url = (
            (og_url and og_url.get("content"))
            or (canonical and canonical.get("href"))
            or None
        )
        if url:
            extra["canonical_url"] = str(url).strip()

        # og:image
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            extra["og_image"] = str(og_image["content"]).strip()

        # Language
        lang: Optional[str] = None
        html_tag = soup.find("html")
        if html_tag and html_tag.get("lang"):
            lang = str(html_tag["lang"]).strip()

        return DocumentMetadata(
            document_id=base.document_id,
            source_path=base.source_path,
            source_type="html",
            title=title or base.title,
            author=author,
            created_at=base.created_at,
            language=lang,
            extra=extra,
        )

    # ------------------------------------------------------------------
    # Decoding
    # ------------------------------------------------------------------

    def _decode(self, filename: str, raw_bytes: bytes) -> str:
        for encoding in DEFAULT_ENCODING_FALLBACKS:
            try:
                return raw_bytes.decode(encoding)
            except UnicodeDecodeError:
                continue
        logger.warning(
            "Could not decode %s with known encodings; using utf-8 with replacement",
            filename,
        )
        return raw_bytes.decode("utf-8", errors="replace")


__all__ = ["HtmlExtractor"]
