import os
from typing import Dict, Any

from connectors.base.metadata import ConnectorFileMetadata

# A basic exclusion list for common binary or non-text files
BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".pdf",
    ".zip", ".tar", ".gz", ".rar", ".7z",
    ".exe", ".dll", ".so", ".dylib", ".class", ".jar", ".war",
    ".mp3", ".mp4", ".mov", ".avi", ".wav",
    ".pyc", ".pyd", ".o", ".obj", ".a", ".lib",
    ".ttf", ".woff", ".woff2", ".eot",
    ".db", ".sqlite", ".sqlite3"
}

def is_indexable_file(filename: str) -> bool:
    """Determine if a file should be indexed based on its extension."""
    _, ext = os.path.splitext(filename.lower())
    return ext not in BINARY_EXTENSIONS

def map_github_file(item: Dict[str, Any], repo_full_name: str) -> ConnectorFileMetadata:
    """
    Map a GitHub file tree item to ConnectorFileMetadata.
    """
    path = item.get("path", "")
    sha = item.get("sha", "")
    size = item.get("size", 0)
    
    # We will fetch the raw file content in the adapter's download_file
    
    return ConnectorFileMetadata(
        external_id=f"repo:{repo_full_name}:blob:{sha}",
        name=os.path.basename(path),
        mime_type="text/plain",  # Defaulting to plain text; could be inferred from ext
        size_bytes=size,
        external_path=f"/{repo_full_name}/{path}",
        raw_metadata={
            "repo": repo_full_name,
            "type": "file",
            "sha": sha,
            "path": path,
            "url": item.get("url", "")
        }
    )

def map_github_release(release: Dict[str, Any], repo_full_name: str) -> ConnectorFileMetadata:
    """
    Map a GitHub release to ConnectorFileMetadata.
    """
    release_id = release.get("id", "")
    tag_name = release.get("tag_name", "")
    name = release.get("name", "") or tag_name
    body = release.get("body", "")
    
    return ConnectorFileMetadata(
        external_id=f"repo:{repo_full_name}:release:{release_id}",
        name=f"Release: {name}",
        mime_type="text/markdown",
        size_bytes=len(body.encode('utf-8')) if body else 0,
        external_path=f"/{repo_full_name}/releases/{tag_name}",
        raw_metadata={
            "repo": repo_full_name,
            "type": "release",
            "release_id": release_id,
            "tag_name": tag_name,
            "published_at": release.get("published_at", ""),
            "markdown_content": body # Cached for download_file
        }
    )
