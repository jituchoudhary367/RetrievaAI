"""
pipeline/extractors/pdf_extractor.py

Extracts text, tables, and metadata from PDF files.

Fits into the ingestion pipeline as the extractor registered for .pdf files.
`pipeline/ingest.py` calls `PdfExtractor().extract(path)` which returns a
normalized `ExtractionResult` that the rest of the pipeline (preprocessor,
deduplicator, chunker) consumes without needing to know the source format.

Dependency chain (all optional — module is importable without any of them):
  pypdf          → primary text extraction
  pdfplumber     → table extraction
  pdf2image      → convert PDF pages to PIL images for OCR
  pytesseract    → OCR on the PIL images
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from pipeline.extractors.text_extractor import (
    BaseExtractor,
    ExtractionError,
    ExtractionResult,
)
from app.models import DocumentMetadata

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional-dependency sentinels
# ---------------------------------------------------------------------------
_PYPDF_AVAILABLE = False
_PDFPLUMBER_AVAILABLE = False
_OCR_AVAILABLE = False

# Minimum extractable characters per page before OCR is attempted
_MIN_CHARS_PER_PAGE = 20


class PdfExtractor(BaseExtractor):
    """
    Extracts plain text, tables, and metadata from PDF documents.

    Strategy (in order):
    1. ``pypdf``      — fast, dependency-light text layer extraction.
    2. ``pdfplumber`` — table detection on every page.
    3. ``pdf2image`` + ``pytesseract`` — OCR on pages that yielded fewer than
       `_MIN_CHARS_PER_PAGE` characters from the text layer (scanned PDFs).

    Any of the three libraries may be absent; the extractor degrades
    gracefully and logs a warning rather than raising.
    """

    supported_extensions = frozenset({".pdf"})

    def __init__(self, max_file_size_bytes: Optional[int] = None) -> None:
        from app.config import get_settings
        settings = get_settings()
        self.max_file_size_bytes = max_file_size_bytes or getattr(
            settings, "max_ingest_file_size_bytes", 50 * 1024 * 1024
        )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def extract(self, file_path: Path) -> ExtractionResult:
        self._validate_file(file_path, self.max_file_size_bytes)
        warnings: List[str] = []
        tables: List[List[List[str]]] = []
        images: List[bytes] = []

        try:
            page_texts, metadata, pdf_warnings = self._extract_with_pypdf(file_path)
            warnings.extend(pdf_warnings)
        except ImportError as exc:
            raise ImportError(str(exc)) from exc
        except ExtractionError:
            raise
        except Exception as exc:
            logger.exception("pypdf failed on %s", file_path)
            raise ExtractionError(f"Failed to extract PDF {file_path}: {exc}") from exc

        # Table extraction via pdfplumber
        try:
            tables = self._extract_tables(file_path, len(page_texts))
        except ImportError as e:
            warnings.append(str(e))
        except Exception as exc:
            logger.warning("pdfplumber table extraction failed for %s: %s", file_path, exc)
            warnings.append(f"Table extraction skipped: {exc}")

        # OCR fallback for pages with sparse text
        page_texts, ocr_warnings = self._ocr_sparse_pages(file_path, page_texts)
        warnings.extend(ocr_warnings)

        full_text = "\n\n".join(t for t in page_texts if t.strip())
        if not full_text.strip():
            raise ExtractionError(f"No extractable text found in {file_path}")

        return ExtractionResult(
            text=full_text,
            metadata=metadata,
            tables=tables,
            images=images,
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # pypdf text extraction
    # ------------------------------------------------------------------

    def _extract_with_pypdf(
        self, file_path: Path
    ) -> tuple[List[str], DocumentMetadata, List[str]]:
        try:
            # pyrefly: ignore [missing-import]
            import pypdf  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "pypdf is required for PDF extraction. "
                "Install it with: pip install pypdf"
            ) from exc

        warnings: List[str] = []
        page_texts: List[str] = []

        with open(file_path, "rb") as fh:
            reader = pypdf.PdfReader(fh)
            info = reader.metadata or {}
            num_pages = len(reader.pages)

            for i, page in enumerate(reader.pages):
                try:
                    text = page.extract_text() or ""
                    page_texts.append(text)
                except Exception as exc:  # noqa: BLE001
                    warnings.append(f"Page {i + 1}: text extraction failed ({exc})")
                    page_texts.append("")

            metadata = self._build_metadata(file_path, info, num_pages)
            return page_texts, metadata, warnings

    # ------------------------------------------------------------------
    # Table extraction via pdfplumber
    # ------------------------------------------------------------------

    def _extract_tables(
        self, file_path: Path, num_pages: int
    ) -> List[List[List[str]]]:
        try:
            # pyrefly: ignore [missing-import]
            import pdfplumber  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "pdfplumber is required for PDF table extraction. "
                "Install it with: pip install pdfplumber"
            ) from exc

        all_tables: List[List[List[str]]] = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_tables = page.extract_tables() or []
                for table in page_tables:
                    # Normalize cells: replace None with ""
                    normalized = [
                        [cell if cell is not None else "" for cell in row]
                        for row in table
                        if row
                    ]
                    if normalized:
                        all_tables.append(normalized)
        return all_tables

    # ------------------------------------------------------------------
    # OCR fallback via pdf2image + pytesseract
    # ------------------------------------------------------------------

    def _ocr_sparse_pages(
        self, file_path: Path, page_texts: List[str]
    ) -> tuple[List[str], List[str]]:
        sparse_indices = [
            i for i, t in enumerate(page_texts)
            if len(t.strip()) < _MIN_CHARS_PER_PAGE
        ]
        if not sparse_indices:
            return page_texts, []

        try:
            # pyrefly: ignore [missing-import]
            from pdf2image import convert_from_path  # noqa: PLC0415
            # pyrefly: ignore [missing-import]
            import pytesseract  # noqa: PLC0415
        except ImportError:
            msg = (
                f"{len(sparse_indices)} page(s) have sparse text but "
                "pdf2image/pytesseract are not installed — OCR skipped. "
                "Install with: pip install pdf2image pytesseract"
            )
            logger.warning(msg)
            return page_texts, [msg]

        warnings: List[str] = []
        result = list(page_texts)
        try:
            images = convert_from_path(
                file_path,
                first_page=min(sparse_indices) + 1,
                last_page=max(sparse_indices) + 1,
                dpi=200,
            )
            img_map = {
                min(sparse_indices) + idx: img
                for idx, img in enumerate(images)
            }
            for page_idx in sparse_indices:
                img = img_map.get(page_idx)
                if img is None:
                    continue
                try:
                    ocr_text = pytesseract.image_to_string(img)
                    result[page_idx] = ocr_text
                except Exception as exc:  # noqa: BLE001
                    warnings.append(f"OCR failed on page {page_idx + 1}: {exc}")
        except Exception as exc:  # noqa: BLE001
            logger.warning("pdf2image conversion failed for %s: %s", file_path, exc)
            warnings.append(f"OCR conversion failed: {exc}")

        return result, warnings

    # ------------------------------------------------------------------
    # Metadata helper
    # ------------------------------------------------------------------

    def _build_metadata(
        self, file_path: Path, info: Any, num_pages: int
    ) -> DocumentMetadata:
        base = self._base_metadata(file_path, "pdf")
        title = _pdf_info_str(info, "/Title") or base.title
        author = _pdf_info_str(info, "/Author")
        extra: Dict[str, Any] = dict(base.extra)
        extra["page_count"] = num_pages
        subject = _pdf_info_str(info, "/Subject")
        if subject:
            extra["subject"] = subject
        creator = _pdf_info_str(info, "/Creator")
        if creator:
            extra["creator"] = creator
        return DocumentMetadata(
            document_id=base.document_id,
            source_path=base.source_path,
            source_type="pdf",
            title=title,
            author=author,
            created_at=base.created_at,
            extra=extra,
        )


def _pdf_info_str(info: Any, key: str) -> Optional[str]:
    """Safely extract a string value from a pypdf info dict."""
    val = info.get(key) if info else None
    if val is None:
        return None
    return str(val).strip() or None


__all__ = ["PdfExtractor"]
