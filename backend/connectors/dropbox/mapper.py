import os
from typing import Dict, Any

from connectors.base.metadata import ConnectorFileMetadata

# Extensions that we skip — same philosophy as GitHub connector
BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".bmp", ".webp", ".tiff",
    ".mp3", ".mp4", ".mov", ".avi", ".wav", ".flac", ".mkv",
    ".zip", ".tar", ".gz", ".rar", ".7z", ".bz2",
    ".exe", ".dll", ".so", ".dylib", ".class", ".jar",
    ".pyc", ".pyd", ".o", ".obj",
    ".db", ".sqlite", ".sqlite3",
    ".ttf", ".woff", ".woff2", ".eot",
}


def is_indexable(path: str) -> bool:
    """Return True if the file at this path should be indexed."""
    _, ext = os.path.splitext(path.lower())
    return ext not in BINARY_EXTENSIONS


def map_dropbox_file(entry: Dict[str, Any]) -> ConnectorFileMetadata:
    """
    Map a Dropbox file metadata entry (from list_folder or delta) to
    a ConnectorFileMetadata object.

    Dropbox file entries look like:
    {
        ".tag": "file",
        "name": "notes.md",
        "path_lower": "/work/notes.md",
        "id": "id:abc123",
        "size": 1024,
        "server_modified": "2024-01-01T00:00:00Z",
        "content_hash": "abcdef..."
    }
    """
    file_id = entry.get("id", "")
    name = entry.get("name", "")
    path = entry.get("path_lower", entry.get("path_display", ""))
    size = entry.get("size", 0)
    content_hash = entry.get("content_hash", "")
    server_modified = entry.get("server_modified", "")

    # Infer MIME type from extension
    _, ext = os.path.splitext(name.lower())
    mime_map = {
        ".md": "text/markdown",
        ".txt": "text/plain",
        ".html": "text/html",
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".csv": "text/csv",
        ".json": "application/json",
        ".py": "text/x-python",
        ".js": "text/javascript",
        ".ts": "text/typescript",
    }
    mime_type = mime_map.get(ext, "application/octet-stream")

    return ConnectorFileMetadata(
        external_id=file_id,
        name=name,
        mime_type=mime_type,
        size_bytes=size,
        external_path=path,
        raw_metadata={
            "type": "file",
            "path_lower": path,
            "content_hash": content_hash,
            "server_modified": server_modified,
        }
    )


def map_dropbox_deleted(entry: Dict[str, Any]) -> str:
    """
    From a deleted delta entry, return the external_id.
    Deleted entries don't have an 'id' so we use path_lower as the key.
    """
    return entry.get("path_lower", "")
