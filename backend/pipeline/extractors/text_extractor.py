"""
pipeline/extractors/text_extractor.py

Extracts plain-text-like documents: .txt, .md, .markdown, .csv, .tsv,
.json, .jsonl.

This module is implemented FIRST in the ingestion pipeline because it has
no third-party parsing dependency (unlike pdf_extractor / docx_extractor /
image_extractor) and therefore doubles as the place where the shared
extractor interface lives:

    - `BaseExtractor`     — common ABC every extractor implements
    - `ExtractionResult`  — normalized output every extractor returns
    - `ExtractionError`   — common failure type

`pipeline/ingest.py` dispatches an input file to the first registered
extractor whose `supports()` returns True, then works only with
`ExtractionResult` from that point on — it never needs to know which
concrete extractor produced it.
"""

from __future__ import annotations

import csv
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional, Tuple

from app.config import get_settings
from app.models import DocumentMetadata

logger = logging.getLogger(__name__)

DEFAULT_ENCODING_FALLBACKS: Tuple[str, ...] = ("utf-8", "utf-8-sig", "latin-1")
DEFAULT_MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB


# --------------------------------------------------------------------------- #
# Shared exceptions
# --------------------------------------------------------------------------- #

class ExtractionError(Exception):
    """Raised when a document cannot be extracted into usable text."""


# --------------------------------------------------------------------------- #
# Shared result type
# --------------------------------------------------------------------------- #

@dataclass
class ExtractionResult:
    """
    Normalized output of any extractor in `pipeline/extractors/`.

    `text` is always populated with a best-effort plain-text rendering
    suitable for downstream chunking, even for structured formats like
    CSV/JSON (rendered as readable tables / pretty-printed JSON) — the
    chunker should never need format-specific logic.
    """

    text: str
    metadata: DocumentMetadata
    # Each table is a list of rows; each row is a list of cell strings.
    tables: List[List[List[str]]] = field(default_factory=list)
    images: List[bytes] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Shared extractor interface
# --------------------------------------------------------------------------- #

class BaseExtractor(ABC):
    """
    Common interface implemented by every extractor under
    `pipeline/extractors/` (text, pdf, html, docx, image).
    """

    #: Lowercase file extensions (with leading dot) this extractor handles.
    supported_extensions: frozenset = frozenset()

    def supports(self, file_path: Path) -> bool:
        """Whether this extractor can handle the given file."""
        return file_path.suffix.lower() in self.supported_extensions

    @abstractmethod
    def extract(self, file_path: Path) -> ExtractionResult:
        """Extract normalized text (and optional tables/images) from a file."""
        raise NotImplementedError

    # -- shared helpers available to all subclasses -------------------- #

    def _base_metadata(self, file_path: Path, source_type: str) -> DocumentMetadata:
        stat = file_path.stat()
        return DocumentMetadata(
            source_path=str(file_path.resolve()),
            source_type=source_type,
            title=file_path.stem,
            created_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
            extra={"size_bytes": stat.st_size},
        )

    def _validate_file(self, file_path: Path, max_file_size_bytes: int) -> int:
        if not file_path.exists():
            raise ExtractionError(f"File not found: {file_path}")
        if not file_path.is_file():
            raise ExtractionError(f"Not a regular file: {file_path}")
        size = file_path.stat().st_size
        if size == 0:
            raise ExtractionError(f"File is empty: {file_path}")
        if size > max_file_size_bytes:
            raise ExtractionError(
                f"File {file_path} exceeds max ingest size "
                f"({size} > {max_file_size_bytes} bytes)"
            )
        return size


# --------------------------------------------------------------------------- #
# Text/CSV/JSON extractor
# --------------------------------------------------------------------------- #

class TextExtractor(BaseExtractor):
    """Extractor for plain-text, markdown, delimited, and JSON files."""

    supported_extensions = frozenset(
        {".txt", ".md", ".markdown", ".csv", ".tsv", ".json", ".jsonl"}
    )

    def __init__(self, max_file_size_bytes: Optional[int] = None) -> None:
        settings = get_settings()
        # `max_ingest_file_size_bytes` is an optional setting — fall back to
        # a sane default if the field hasn't been added to Settings yet.
        self.max_file_size_bytes = max_file_size_bytes or getattr(
            settings, "max_ingest_file_size_bytes", DEFAULT_MAX_FILE_SIZE_BYTES
        )

    def extract(self, file_path: Path) -> ExtractionResult:
        self._validate_file(file_path, self.max_file_size_bytes)
        suffix = file_path.suffix.lower()
        warnings: List[str] = []

        try:
            if suffix == ".txt":
                text = self._read_text(file_path, warnings)
                metadata = self._base_metadata(file_path, "text")
                return ExtractionResult(text=text, metadata=metadata, warnings=warnings)

            if suffix in {".md", ".markdown"}:
                text = self._read_text(file_path, warnings)
                metadata = self._base_metadata(file_path, "md")
                return ExtractionResult(text=text, metadata=metadata, warnings=warnings)

            if suffix in {".csv", ".tsv"}:
                text, tables = self._read_delimited(file_path, suffix, warnings)
                metadata = self._base_metadata(file_path, "csv")
                return ExtractionResult(
                    text=text, metadata=metadata, tables=tables, warnings=warnings
                )

            if suffix in {".json", ".jsonl"}:
                text = self._read_json(file_path, suffix, warnings)
                metadata = self._base_metadata(file_path, "json")
                return ExtractionResult(text=text, metadata=metadata, warnings=warnings)

        except ExtractionError:
            raise
        except Exception as exc:  # noqa: BLE001 - convert to domain error
            logger.exception("Unexpected failure extracting %s", file_path)
            raise ExtractionError(f"Failed to extract {file_path}: {exc}") from exc

        raise ExtractionError(f"Unsupported extension for TextExtractor: {suffix}")

    # -- format-specific readers ----------------------------------------- #

    def _read_text(self, file_path: Path, warnings: List[str]) -> str:
        raw_bytes = file_path.read_bytes()
        for encoding in DEFAULT_ENCODING_FALLBACKS:
            try:
                return raw_bytes.decode(encoding)
            except UnicodeDecodeError:
                continue
        warnings.append(
            f"Could not decode {file_path.name} with known encodings "
            f"{DEFAULT_ENCODING_FALLBACKS}; decoding as utf-8 with "
            "replacement characters."
        )
        return raw_bytes.decode("utf-8", errors="replace")

    def _read_delimited(
        self, file_path: Path, suffix: str, warnings: List[str]
    ) -> Tuple[str, List[List[List[str]]]]:
        delimiter = "\t" if suffix == ".tsv" else ","
        raw_text = self._read_text(file_path, warnings)

        try:
            reader = csv.reader(raw_text.splitlines(), delimiter=delimiter)
            rows = [row for row in reader if row]
        except csv.Error as exc:
            raise ExtractionError(
                f"Failed to parse delimited file {file_path}: {exc}"
            ) from exc

        if not rows:
            warnings.append(f"{file_path.name} contained no parseable rows.")
            return "", []

        header, *data_rows = rows
        col_count = len(header)
        malformed = [i for i, row in enumerate(data_rows) if len(row) != col_count]
        if malformed:
            warnings.append(
                f"{len(malformed)} row(s) in {file_path.name} had a column "
                f"count different from the header ({col_count}); they were "
                "kept as-is."
            )

        # Render as a readable pipe-delimited table so structured rows read
        # naturally as text for downstream chunking / embedding.
        lines = [" | ".join(header), " | ".join("-" * max(len(c), 3) for c in header)]
        lines.extend(" | ".join(row) for row in data_rows)
        text = "\n".join(lines)
        return text, [rows]

    def _read_json(self, file_path: Path, suffix: str, warnings: List[str]) -> str:
        raw_text = self._read_text(file_path, warnings)

        if suffix == ".jsonl":
            records: List[Any] = []
            for line_no, line in enumerate(raw_text.splitlines(), start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    warnings.append(
                        f"Skipped malformed JSONL line {line_no} in "
                        f"{file_path.name}: {exc}"
                    )
            if not records:
                raise ExtractionError(f"No valid JSONL records found in {file_path}")
            return "\n\n".join(
                json.dumps(record, indent=2, ensure_ascii=False) for record in records
            )

        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise ExtractionError(f"Invalid JSON in {file_path}: {exc}") from exc
        return json.dumps(parsed, indent=2, ensure_ascii=False)


__all__ = [
    "BaseExtractor",
    "ExtractionResult",
    "ExtractionError",
    "TextExtractor",
    "DEFAULT_MAX_FILE_SIZE_BYTES",
]