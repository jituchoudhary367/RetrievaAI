import os
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


def is_indexable(blob_name: str) -> bool:
    _, ext = os.path.splitext(blob_name.lower())
    return ext not in BINARY_EXTENSIONS


def map_azure_blob(container: str, blob: Dict[str, Any]) -> ConnectorFileMetadata:
    """
    Map an Azure Blob Storage blob metadata dict to ConnectorFileMetadata.

    blob keys: name, size, etag, last_modified, content_type
    """
    name = blob.get("name", "")
    size = blob.get("size", 0)
    etag = blob.get("etag", "").strip('"')
    last_modified = str(blob.get("last_modified", ""))
    content_type = blob.get("content_type", "") or "application/octet-stream"

    # Infer from extension if content_type is generic
    if content_type in ("application/octet-stream", ""):
        _, ext = os.path.splitext(name.lower())
        mime_map = {
            ".txt": "text/plain", ".md": "text/markdown", ".html": "text/html",
            ".pdf": "application/pdf", ".csv": "text/csv", ".json": "application/json",
        }
        content_type = mime_map.get(ext, "application/octet-stream")

    basename = os.path.basename(name) or name

    return ConnectorFileMetadata(
        external_id=f"azure://{container}/{name}",
        name=basename,
        mime_type=content_type,
        size_bytes=size,
        external_path=f"/{container}/{name}",
        raw_metadata={
            "provider": "azure_blob",
            "container": container,
            "blob_name": name,
            "etag": etag,
            "last_modified": last_modified,
        }
    )


def map_azure_event_grid(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse an Azure Event Grid event for Blob Storage.

    Event types:
      Microsoft.Storage.BlobCreated  -> action='put'
      Microsoft.Storage.BlobDeleted  -> action='delete'

    subject format: /blobServices/default/containers/{container}/blobs/{blob}
    """
    event_type = event.get("eventType", "")
    subject = event.get("subject", "")
    data = event.get("data", {})

    # Parse container and blob from subject
    # subject: /blobServices/default/containers/my-container/blobs/path/to/file.txt
    container = ""
    blob_name = ""
    if "/containers/" in subject and "/blobs/" in subject:
        after_containers = subject.split("/containers/", 1)[1]
        container, _, blob_name = after_containers.partition("/blobs/")

    action = "delete" if "Deleted" in event_type else "put"

    return {
        "action": action,
        "container": container,
        "blob_name": blob_name,
        "content_length": data.get("contentLength", 0),
        "etag": data.get("eTag", ""),
        "content_type": data.get("contentType", ""),
    }
