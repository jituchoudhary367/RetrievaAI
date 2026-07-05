"""
pipeline/extractors/image_extractor.py

Extracts text from image files via OCR (pytesseract + Pillow) and records
per-word confidence, image dimensions, and colour mode as metadata.

Fits into the ingestion pipeline as the extractor registered for common image
formats (.png, .jpg, .jpeg, .tiff, .bmp, .gif, .webp).

Dependencies (both optional — module is always importable):
  Pillow       → image loading and basic property inspection
  pytesseract  → Tesseract OCR engine wrapper
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional

from pipeline.extractors.text_extractor import (
    BaseExtractor,
    ExtractionError,
    ExtractionResult,
)
from app.models import DocumentMetadata

logger = logging.getLogger(__name__)

# Average OCR confidence below this value triggers a metadata warning flag
_LOW_CONFIDENCE_THRESHOLD = 50.0


class ImageExtractor(BaseExtractor):
    """
    Extracts text from image files using Tesseract OCR via ``pytesseract``.

    Word-level bounding boxes and confidence scores are obtained via
    ``image_to_data`` and summarised in the metadata extra dict.  Images
    with a mean word confidence below ``_LOW_CONFIDENCE_THRESHOLD`` have
    ``low_ocr_confidence=True`` set in their metadata so downstream
    pipeline stages can treat them with appropriate scepticism.
    """

    supported_extensions = frozenset(
        {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".gif", ".webp"}
    )

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

        try:
            from PIL import Image  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "Pillow is required for image extraction. "
                "Install it with: pip install Pillow"
            ) from exc

        try:
            import pytesseract  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "pytesseract is required for image OCR. "
                "Install it with: pip install pytesseract"
            ) from exc

        warnings: List[str] = []

        try:
            img = Image.open(file_path)
            img.load()
        except Exception as exc:
            raise ExtractionError(
                f"Failed to open image {file_path}: {exc}"
            ) from exc

        width, height = img.size
        mode = img.mode

        # Convert to RGB if necessary for best Tesseract results
        if mode not in ("RGB", "L"):
            try:
                img = img.convert("RGB")
                warnings.append(f"Converted image from {mode} to RGB for OCR.")
            except Exception as exc:  # noqa: BLE001
                warnings.append(f"Image mode conversion failed ({exc}); attempting OCR as-is.")

        # Run OCR with word-level data
        text, avg_confidence, ocr_warnings = self._run_ocr(img, file_path.name, pytesseract)
        warnings.extend(ocr_warnings)

        if not text.strip():
            raise ExtractionError(f"No text found in image {file_path}")

        metadata = self._build_metadata(
            file_path, width, height, mode, avg_confidence
        )

        return ExtractionResult(
            text=text,
            metadata=metadata,
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # OCR
    # ------------------------------------------------------------------

    def _run_ocr(
        self, img: object, filename: str, pytesseract: object
    ) -> tuple[str, float, List[str]]:
        """
        Returns (full_text, mean_confidence, warnings).
        Uses image_to_data for word-level confidence, then image_to_string
        for the clean text output.
        """
        import pandas  # noqa: F401 — pytesseract.image_to_data may use pandas

        warnings: List[str] = []
        avg_confidence = 0.0

        try:
            # pandas output_type for image_to_data
            data = pytesseract.image_to_data(
                img, output_type=pytesseract.Output.DICT
            )
            confidences = [
                int(c) for c in data.get("conf", []) if str(c).lstrip("-").isdigit() and int(c) >= 0
            ]
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
                if avg_confidence < _LOW_CONFIDENCE_THRESHOLD:
                    warnings.append(
                        f"Low average OCR confidence ({avg_confidence:.1f}%) for {filename}."
                    )
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"image_to_data failed ({exc}); confidence unavailable.")

        try:
            text = pytesseract.image_to_string(img)
        except Exception as exc:
            raise ExtractionError(f"pytesseract OCR failed on {filename}: {exc}") from exc

        return text, avg_confidence, warnings

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def _build_metadata(
        self,
        file_path: Path,
        width: int,
        height: int,
        mode: str,
        avg_confidence: float,
    ) -> DocumentMetadata:
        base = self._base_metadata(file_path, "image")
        extra: Dict = dict(base.extra)
        extra["width"] = width
        extra["height"] = height
        extra["mode"] = mode
        extra["avg_ocr_confidence"] = round(avg_confidence, 2)
        extra["low_ocr_confidence"] = avg_confidence < _LOW_CONFIDENCE_THRESHOLD

        return DocumentMetadata(
            document_id=base.document_id,
            source_path=base.source_path,
            source_type="image",
            title=base.title,
            created_at=base.created_at,
            extra=extra,
        )


__all__ = ["ImageExtractor"]
