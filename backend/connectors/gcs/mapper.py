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


def is_indexable(name: str) -> bool:
    _, ext = os.path.splitext(name.lower())
    return ext not in BINARY_EXTENSIONS


def map_gcs_object(bucket: str, blob: Dict[str, Any]) -> ConnectorFileMetadata:
    """
    Map a GCS blob metadata dict to ConnectorFileMetadata.

    blob keys: name, size, etag, updated, contentType
    """
    name = blob.get("name", "")
    size = int(blob.get("size", 0))
    etag = blob.get("etag", "")
    updated = blob.get("updated", "")
    content_type = blob.get("contentType", "") or "application/octet-stream"

    if content_type == "application/octet-stream":
        _, ext = os.path.splitext(name.lower())
        mime_map = {
            ".txt": "text/plain", ".md": "text/markdown", ".html": "text/html",
            ".pdf": "application/pdf", ".csv": "text/csv", ".json": "application/json",
        }
        content_type = mime_map.get(ext, "application/octet-stream")

    basename = os.path.basename(name) or name

    return ConnectorFileMetadata(
        external_id=f"gs://{bucket}/{name}",
        name=basename,
        mime_type=content_type,
        size_bytes=size,
        external_path=f"/{bucket}/{name}",
        raw_metadata={
            "provider": "gcs",
            "bucket": bucket,
            "object_name": name,
            "etag": etag,
            "updated": updated,
        }
    )


def map_pubsub_notification(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse a GCS Pub/Sub notification message.

    GCS sends Pub/Sub messages with attributes:
    {
        "eventType": "OBJECT_FINALIZE" | "OBJECT_DELETE" | "OBJECT_ARCHIVE" | ...,
        "bucketId": "my-bucket",
        "objectId": "path/to/file.txt",
        "objectSize": "1024",
        "contentType": "text/plain",
        "objectGeneration": "12345",
    }
    """
    attributes = message.get("attributes", {})
    event_type = attributes.get("eventType", "")
    bucket = attributes.get("bucketId", "")
    object_name = attributes.get("objectId", "")
    size = int(attributes.get("objectSize", 0))
    content_type = attributes.get("contentType", "")

    # OBJECT_FINALIZE = create/update; OBJECT_DELETE/OBJECT_ARCHIVE = delete
    action = "delete" if event_type in ("OBJECT_DELETE", "OBJECT_ARCHIVE") else "put"

    return {
        "action": action,
        "bucket": bucket,
        "object_name": object_name,
        "size": size,
        "content_type": content_type,
    }
