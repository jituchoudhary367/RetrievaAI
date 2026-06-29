"""
services/blob_storage.py

Local-filesystem blob storage abstraction (§1.4).

Saves original ingested files so that Preview and Download work against
real bytes, not discarded post-extraction text.

API:
  save(source_path_or_bytes, filename) -> str   (returns the stored path)
  load(path) -> bytes
  delete(path) -> None

The root directory is configured via BLOB_ROOT_PATH (defaults to ./data/blobs).
Files are organised as: <root>/<tenant_id>/<document_id>/<filename>
"""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import Union

from app.config import get_settings

logger = logging.getLogger(__name__)


class BlobStorage:
    """Local-filesystem backed blob storage."""

    def __init__(self) -> None:
        cfg = get_settings()
        self._root = Path(cfg.blob.root_path)
        if not cfg.blob.root_path.is_absolute():
            self._root = (cfg.base_dir / cfg.blob.root_path).resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        data: Union[bytes, Path],
        filename: str,
        tenant_id: str = "default",
        document_id: str = "unknown",
    ) -> str:
        """
        Save *data* (bytes or a source file path) to blob storage.

        Returns the relative path string suitable for storing in the DB.
        """
        dest_dir = self._root / tenant_id / document_id
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / filename

        if isinstance(data, Path):
            shutil.copy2(data, dest)
        else:
            dest.write_bytes(data)

        rel_path = str(dest.relative_to(self._root))
        logger.debug("BlobStorage.save: %s → %s", filename, rel_path)
        return rel_path

    def load(self, path: str) -> bytes:
        """Load and return the bytes for the blob at *path*."""
        full = self._root / path
        if not full.exists():
            raise FileNotFoundError(f"Blob not found: {path}")
        return full.read_bytes()

    def delete(self, path: str) -> None:
        """Delete the blob at *path*. Silently ignores missing files."""
        full = self._root / path
        try:
            full.unlink(missing_ok=True)
            logger.debug("BlobStorage.delete: %s", path)
        except Exception as exc:  # noqa: BLE001
            logger.warning("BlobStorage.delete failed for %s: %s", path, exc)

    def full_path(self, path: str) -> Path:
        """Return the absolute filesystem path for a stored blob."""
        return self._root / path


# Module-level singleton
_blob_storage: BlobStorage | None = None


def get_blob_storage() -> BlobStorage:
    global _blob_storage
    if _blob_storage is None:
        _blob_storage = BlobStorage()
    return _blob_storage


__all__ = ["BlobStorage", "get_blob_storage"]
