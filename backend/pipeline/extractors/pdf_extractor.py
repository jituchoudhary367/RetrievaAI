"""
pipeline/extractors/pdf_extractor.py

Extracts text, tables, and metadata from PDF files.

Fits into the ingestion pipeline as the extractor registered for .pdf files.
`pipeline/ingest.py` calls `PdfExtractor().extract(path)` which returns a
normalized `ExtractionResult` that the rest of the pipeline (preprocessor,
deduplicator, chunker) consumes without needing to know the source format.

Dependency chain (all optional — module is importable without any of them):
  pymupdf        → primary text extraction and table extraction
  paddleocr      → OCR on sparse/scanned pages
"""

from __future__ import annotations

import logging
import threading
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
_PYMUPDF_AVAILABLE = False
_OCR_AVAILABLE = False

# Minimum extractable characters per page before OCR is attempted
_MIN_CHARS_PER_PAGE = 20


class PdfExtractor(BaseExtractor):
    """
    Extracts plain text, tables, and metadata from PDF documents.

    Strategy (in order):
    1. ``PyMuPDF``    — fast, dependency-light text layer extraction.
    2. ``PyMuPDF``    — table detection on every page.
    3. ``PaddleOCR``  — OCR on pages that yielded fewer than
       `_MIN_CHARS_PER_PAGE` characters from the text layer (scanned PDFs).

    Any of the libraries may be absent; the extractor degrades
    gracefully and logs a warning rather than raising.
    """

    supported_extensions = frozenset({".pdf"})

    _ocr_instance = None
    _ocr_lock = threading.Lock()

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
        warnings: List[str] = []
        tables: List[List[List[str]]] = []
        images: List[bytes] = []

        try:
            page_texts, metadata, pdf_warnings = self._extract_with_pymupdf(file_path)
            warnings.extend(pdf_warnings)
        except ImportError as exc:
            raise ImportError(str(exc)) from exc
        except ExtractionError:
            raise
        except Exception as exc:
            logger.exception("PyMuPDF failed on %s", file_path)
            raise ExtractionError(f"Failed to extract PDF {file_path}: {exc}") from exc

        # Table extraction via PyMuPDF
        try:
            tables = self._extract_tables(file_path)
        except ImportError as e:
            warnings.append(str(e))
        except Exception as exc:
            logger.warning("PyMuPDF table extraction failed for %s: %s", file_path, exc)
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
    # PyMuPDF text extraction
    # ------------------------------------------------------------------

    def _extract_with_pymupdf(
        self, file_path: Path
    ) -> tuple[List[str], DocumentMetadata, List[str]]:
        try:
            import fitz  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "PyMuPDF is required for PDF extraction. "
                "Install it with: pip install pymupdf"
            ) from exc

        warnings: List[str] = []
        page_texts: List[str] = []

        with fitz.open(file_path) as doc:
            info = doc.metadata or {}
            num_pages = len(doc)

            for i, page in enumerate(doc):
                try:
                    text = page.get_text() or ""
                    page_texts.append(text)
                except Exception as exc:  # noqa: BLE001
                    warnings.append(f"Page {i + 1}: text extraction failed ({exc})")
                    page_texts.append("")

            metadata = self._build_metadata(file_path, info, num_pages)
            return page_texts, metadata, warnings

    # ------------------------------------------------------------------
    # Table extraction via PyMuPDF
    # ------------------------------------------------------------------

    def _extract_tables(
        self, file_path: Path
    ) -> List[List[List[str]]]:
        try:
            import fitz  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "PyMuPDF is required for PDF table extraction. "
                "Install it with: pip install pymupdf"
            ) from exc

        all_tables: List[List[List[str]]] = []
        with fitz.open(file_path) as doc:
            for page in doc:
                try:
                    tables = page.find_tables()
                    if tables:
                        for table in tables:
                            raw_table = table.extract()
                            # Normalize cells: replace None with ""
                            normalized = [
                                [cell if cell is not None else "" for cell in row]
                                for row in raw_table
                                if row
                            ]
                            if normalized:
                                all_tables.append(normalized)
                except Exception as exc:
                    logger.warning("Table extraction error on a page: %s", exc)
        return all_tables

    # ------------------------------------------------------------------
    # OCR fallback via PaddleOCR
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
            # Preload torch to prevent Windows DLL conflicts (WinError 127) 
            # with paddlepaddle when sentence-transformers imports torch later.
            try:
                import torch  # noqa: PLC0415
            except ImportError:
                pass

            import fitz  # noqa: PLC0415
            import numpy as np  # noqa: PLC0415
            from paddleocr import PaddleOCR  # noqa: PLC0415
        except ImportError:
            msg = (
                f"{len(sparse_indices)} page(s) have sparse text but "
                "paddleocr/pymupdf/numpy are not installed — OCR skipped. "
                "Install with: pip install paddleocr paddlepaddle pymupdf numpy"
            )
            logger.warning(msg)
            return page_texts, [msg]

        warnings: List[str] = []
        result = list(page_texts)
        
        try:
            if PdfExtractor._ocr_instance is None:
                with PdfExtractor._ocr_lock:
                    if PdfExtractor._ocr_instance is None:
                        PdfExtractor._ocr_instance = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
            ocr = PdfExtractor._ocr_instance
        except Exception as exc:
            warnings.append(f"Failed to initialize PaddleOCR: {exc}")
            return result, warnings

        try:
            with fitz.open(file_path) as doc:
                for page_idx in sparse_indices:
                    try:
                        page = doc[page_idx]
                        pix = page.get_pixmap(alpha=False)
                        
                        img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
                        
                        ocr_result = ocr.ocr(img_array, cls=True)
                        
                        text_lines = []
                        if ocr_result and ocr_result[0]:
                            for line in ocr_result[0]:
                                text_lines.append(line[1][0])
                        
                        result[page_idx] = "\n".join(text_lines)
                        
                    except Exception as exc:  # noqa: BLE001
                        warnings.append(f"OCR failed on page {page_idx + 1}: {exc}")
        except Exception as exc:  # noqa: BLE001
            logger.warning("PyMuPDF document opening failed during OCR for %s: %s", file_path, exc)
            warnings.append(f"OCR conversion failed: {exc}")

        return result, warnings

    # ------------------------------------------------------------------
    # Metadata helper
    # ------------------------------------------------------------------

    def _build_metadata(
        self, file_path: Path, info: dict, num_pages: int
    ) -> DocumentMetadata:
        base = self._base_metadata(file_path, "pdf")
        title = str(info.get("title") or "").strip() or base.title
        author = str(info.get("author") or "").strip() or None
        extra: Dict[str, Any] = dict(base.extra)
        extra["page_count"] = num_pages
        subject = str(info.get("subject") or "").strip() or None
        if subject:
            extra["subject"] = subject
        creator = str(info.get("creator") or "").strip() or None
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

__all__ = ["PdfExtractor"]
