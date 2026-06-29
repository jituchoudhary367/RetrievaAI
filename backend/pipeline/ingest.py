"""
pipeline/ingest.py

Orchestrates the full offline ingestion pipeline:
  Extract → Preprocess → Deduplicate → Chunk → Embed → Index

Entry point: ``IngestionPipeline.ingest_path(path, glob, force)``

Key features:
  - Auto-discovers files under a directory using the provided glob pattern.
  - Dispatches each file to the first registered extractor whose
    ``supports()`` returns True.  Missing optional extractor dependencies
    produce a warning, not a crash.
  - Maintains a JSON idempotency manifest (keyed by content hash) so
    unchanged files are skipped on re-ingestion unless ``force=True``.
  - One file's failure is caught and recorded in ``FileIngestResult``; it
    never aborts the batch.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from app.config import get_settings
from pipeline.extractors.text_extractor import BaseExtractor, ExtractionError
from pipeline.preprocessor import Preprocessor
from pipeline.deduplicator import Deduplicator, compute_content_hash
from pipeline.chunker import Chunker
from pipeline.embedder import Embedder
from pipeline.indexer import Indexer

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

@dataclass
class FileIngestResult:
    """Outcome of ingesting a single file."""

    path: str
    status: str  # "indexed" | "skipped" | "failed"
    num_chunks: int = 0
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


@dataclass
class IngestionReport:
    """Aggregate result of an ``ingest_path`` call."""

    total_files: int = 0
    indexed: int = 0
    skipped: int = 0
    failed: int = 0
    results: List[FileIngestResult] = field(default_factory=list)
    elapsed_seconds: float = 0.0


@dataclass
class IngestionManifest:
    """Persisted content-hash → file-path mapping for idempotency."""

    entries: Dict[str, str] = field(default_factory=dict)  # hash → path
    _path: Optional[Path] = field(default=None, repr=False, compare=False)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.entries, fh, indent=2)
        logger.debug("Manifest saved: %d entries.", len(self.entries))

    @classmethod
    def load(cls, path: Path) -> "IngestionManifest":
        if not path.exists():
            return cls(_path=path)
        try:
            with open(path, encoding="utf-8") as fh:
                entries = json.load(fh)
            return cls(entries=entries, _path=path)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load manifest from %s: %s — starting fresh.", path, exc)
            return cls(_path=path)

    def contains_hash(self, content_hash: str) -> bool:
        return content_hash in self.entries

    def record(self, content_hash: str, source_path: str) -> None:
        self.entries[content_hash] = source_path


# ---------------------------------------------------------------------------
# Extractor registry builder
# ---------------------------------------------------------------------------

def _build_extractor_registry() -> List[BaseExtractor]:
    """
    Instantiate every extractor.  Skip extractors whose optional dependencies
    are missing (log a warning instead of crashing).
    """
    from pipeline.extractors.text_extractor import TextExtractor

    extractor_classes = [TextExtractor]

    try:
        from pipeline.extractors.pdf_extractor import PdfExtractor
        extractor_classes.append(PdfExtractor)
    except ImportError as exc:
        logger.warning("PdfExtractor unavailable: %s", exc)

    try:
        from pipeline.extractors.html_extractor import HtmlExtractor
        extractor_classes.append(HtmlExtractor)
    except ImportError as exc:
        logger.warning("HtmlExtractor unavailable: %s", exc)

    try:
        from pipeline.extractors.docx_extractor import DocxExtractor
        extractor_classes.append(DocxExtractor)
    except ImportError as exc:
        logger.warning("DocxExtractor unavailable: %s", exc)

    try:
        from pipeline.extractors.image_extractor import ImageExtractor
        extractor_classes.append(ImageExtractor)
    except ImportError as exc:
        logger.warning("ImageExtractor unavailable: %s", exc)

    registry: List[BaseExtractor] = []
    for cls in extractor_classes:
        try:
            registry.append(cls())
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not instantiate %s: %s", cls.__name__, exc)

    return registry


# ---------------------------------------------------------------------------
# Ingestion pipeline
# ---------------------------------------------------------------------------

class IngestionPipeline:
    """
    Drives the full Extract → Preprocess → Deduplicate → Chunk → Embed →
    Index pipeline.

    Parameters
    ----------
    preprocessor, deduplicator, chunker, embedder, indexer:
        Override individual stages (mainly for testing).
    """

    def __init__(
        self,
        preprocessor: Optional[Preprocessor] = None,
        deduplicator: Optional[Deduplicator] = None,
        chunker: Optional[Chunker] = None,
        embedder: Optional[Embedder] = None,
        indexer: Optional[Indexer] = None,
    ) -> None:
        settings = get_settings()
        self._manifest_path: Path = (
            settings.data_dir / "ingest_manifest.json"
        )
        self._extractors = _build_extractor_registry()
        self._preprocessor = preprocessor or Preprocessor()
        self._deduplicator = deduplicator or Deduplicator()
        self._chunker = chunker or Chunker()
        self._embedder = embedder or Embedder()
        self._indexer = indexer or Indexer()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ingest_path(
        self,
        tenant_id: str,
        path: Path,
        glob: str = "**/*",
        force: bool = False,
    ) -> IngestionReport:
        """
        Ingest all matching files under *path*.

        Parameters
        ----------
        path:
            A file path or directory to scan.
        glob:
            Glob pattern (relative to *path* when it's a directory).
        force:
            If True, re-ingest files whose hash is already in the manifest.
        """
        path = Path(path)
        t_start = time.monotonic()

        manifest = IngestionManifest.load(self._manifest_path)
        report = IngestionReport()

        files = self._collect_files(path, glob)
        report.total_files = len(files)

        if not files:
            logger.info("No files matched pattern '%s' under %s.", glob, path)
            return report

        logger.info("Starting ingestion of %d file(s).", len(files))

        for file_path in files:
            result = self._ingest_file(tenant_id, file_path, manifest, force)
            report.results.append(result)
            if result.status == "indexed":
                report.indexed += 1
            elif result.status == "skipped":
                report.skipped += 1
            else:
                report.failed += 1

        manifest.save(self._manifest_path)
        report.elapsed_seconds = time.monotonic() - t_start
        logger.info(
            "Ingestion complete: %d indexed, %d skipped, %d failed in %.1fs.",
            report.indexed,
            report.skipped,
            report.failed,
            report.elapsed_seconds,
        )
        return report

    # ------------------------------------------------------------------
    # Per-file ingestion
    # ------------------------------------------------------------------

    def _ingest_file(
        self,
        tenant_id: str,
        file_path: Path,
        manifest: IngestionManifest,
        force: bool,
    ) -> FileIngestResult:
        str_path = str(file_path)

        # --- Find a matching extractor ---
        extractor = next(
            (e for e in self._extractors if e.supports(file_path)), None
        )
        if extractor is None:
            logger.debug("No extractor for %s — skipping.", file_path)
            return FileIngestResult(path=str_path, status="skipped",
                                    error="No extractor registered for this file type")

        try:
            # --- Extract ---
            extraction_result = extractor.extract(file_path)

            # --- Idempotency check ---
            content_hash = compute_content_hash(extraction_result.text)
            manifest_key = f"{tenant_id}:{content_hash}"
            if not force and manifest.contains_hash(manifest_key):
                logger.debug("Skipping unchanged file %s (hash match).", file_path)
                return FileIngestResult(path=str_path, status="skipped")

            # --- Preprocess ---
            prep = self._preprocessor.process(extraction_result.text)
            warnings = list(extraction_result.warnings) + list(prep.warnings)

            if not prep.text.strip():
                return FileIngestResult(
                    path=str_path,
                    status="failed",
                    error="Empty text after preprocessing",
                    warnings=warnings,
                )

            # --- Deduplicate at document level (single item) ---
            dedup = self._deduplicator.deduplicate(
                [prep.text], text_fn=lambda t: t
            )
            if not dedup.kept:
                return FileIngestResult(path=str_path, status="skipped",
                                        warnings=warnings)

            # --- Chunk ---
            source_type = extraction_result.metadata.source_type
            document_id = extraction_result.metadata.document_id
            chunks = self._chunker.chunk_document(
                prep.text, document_id, source_type=source_type
            )

            if not chunks:
                return FileIngestResult(
                    path=str_path,
                    status="failed",
                    error="No chunks produced after chunking",
                    warnings=warnings,
                )

            # Assign tenant_id to document metadata and chunks
            extraction_result.metadata.tenant_id = tenant_id
            for chunk in chunks:
                chunk.tenant_id = tenant_id

            # Enrich chunk metadata with document metadata
            meta_dict = {
                "source_path": extraction_result.metadata.source_path,
                "source_type": source_type,
                "title": extraction_result.metadata.title or "",
                "author": extraction_result.metadata.author or "",
            }
            for chunk in chunks:
                chunk.metadata.update(meta_dict)

            # --- Embed ---
            chunks = self._embedder.embed_chunks(chunks)

            # --- Index ---
            count = self._indexer.index_chunks(chunks)

            # --- Record in manifest ---
            manifest.record(manifest_key, str_path)

            return FileIngestResult(
                path=str_path,
                status="indexed",
                num_chunks=count,
                warnings=warnings,
            )

        except ExtractionError as exc:
            logger.warning("Extraction failed for %s: %s", file_path, exc)
            return FileIngestResult(path=str_path, status="failed", error=str(exc))
        except Exception as exc:  # noqa: BLE001
            logger.error("Unexpected error ingesting %s: %s", file_path, exc, exc_info=True)
            return FileIngestResult(path=str_path, status="failed", error=str(exc))

    # ------------------------------------------------------------------
    # File discovery
    # ------------------------------------------------------------------

    @staticmethod
    def _collect_files(path: Path, glob: str) -> List[Path]:
        if path.is_file():
            return [path]
        if path.is_dir():
            return sorted(
                f for f in path.glob(glob) if f.is_file()
            )
        logger.warning("Path does not exist or is not a file/dir: %s", path)
        return []


__all__ = [
    "IngestionPipeline",
    "IngestionReport",
    "FileIngestResult",
    "IngestionManifest",
]
