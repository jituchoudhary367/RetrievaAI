import os
import hashlib
from typing import Dict, Any

from connectors.base.metadata import ConnectorFileMetadata

BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".bmp", ".webp",
    ".mp3", ".mp4", ".mov", ".avi", ".wav", ".mkv",
    ".zip", ".tar", ".gz", ".rar", ".7z", ".bz2",
    ".exe", ".dll", ".so", ".dylib", ".class", ".jar",
    ".pyc", ".db", ".sqlite", ".sqlite3",
    ".ttf", ".woff", ".woff2", ".eot",
}

def is_indexable(path: str) -> bool:
    _, ext = os.path.splitext(path.lower())
    return ext not in BINARY_EXTENSIONS

def compute_checksum(file_path: str) -> str:
    """Compute SHA-256 checksum of a file's contents."""
    if not os.path.exists(file_path):
        return ""
    hash_sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except OSError:
        return ""

def map_filesystem_file(file_path: str, root_dir: str, checksum: str = "") -> ConnectorFileMetadata:
    """
    Map a local file to ConnectorFileMetadata.
    Uses the checksum as the primary external_id to deduplicate renames/moves.
    """
    if not checksum:
        checksum = compute_checksum(file_path)
        
    stat = os.stat(file_path) if os.path.exists(file_path) else None
    size = stat.st_size if stat else 0
    mtime = str(stat.st_mtime) if stat else ""
    
    name = os.path.basename(file_path)
    _, ext = os.path.splitext(name.lower())
    
    mime_map = {
        ".txt": "text/plain", ".md": "text/markdown", ".html": "text/html",
        ".pdf": "application/pdf", ".csv": "text/csv", ".json": "application/json",
        ".py": "text/x-python", ".js": "text/javascript", ".ts": "text/typescript",
    }
    mime_type = mime_map.get(ext, "application/octet-stream")
    
    # Calculate path relative to the root directory for consistency
    rel_path = os.path.relpath(file_path, root_dir)
    
    # If the file is empty or we couldn't read it, fallback to path-based ID
    ext_id = f"fs://{checksum}" if checksum else f"fs-path://{rel_path}"

    return ConnectorFileMetadata(
        external_id=ext_id,
        name=name,
        mime_type=mime_type,
        size_bytes=size,
        external_path=file_path,
        raw_metadata={
            "provider": "filesystem",
            "root_dir": root_dir,
            "relative_path": rel_path,
            "checksum": checksum,
            "mtime": mtime,
        }
    )

def map_filesystem_event(event_type: str, src_path: str, dest_path: str = "") -> Dict[str, Any]:
    """
    Parse a filesystem event (e.g. from watchdog).
    """
    action = "delete" if event_type in ("deleted", "moved_from") else "put"
    
    # For a move event, watchdog provides both src_path (old) and dest_path (new)
    # The adapter can handle the delete of the old path and put of the new path.
    return {
        "action": action,
        "src_path": src_path,
        "dest_path": dest_path,
        "event_type": event_type,
    }
