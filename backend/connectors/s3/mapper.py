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


def is_indexable(key: str) -> bool:
    _, ext = os.path.splitext(key.lower())
    return ext not in BINARY_EXTENSIONS


def map_s3_object(bucket: str, obj: Dict[str, Any]) -> ConnectorFileMetadata:
    """
    Map an S3 object metadata dict (from list_objects_v2) to ConnectorFileMetadata.

    obj keys: Key, Size, ETag, LastModified, StorageClass
    """
    key = obj.get("Key", "")
    size = obj.get("Size", 0)
    etag = obj.get("ETag", "").strip('"')
    last_modified = str(obj.get("LastModified", ""))

    name = os.path.basename(key) or key
    _, ext = os.path.splitext(name.lower())
    mime_map = {
        ".txt": "text/plain", ".md": "text/markdown", ".html": "text/html",
        ".pdf": "application/pdf", ".csv": "text/csv", ".json": "application/json",
        ".py": "text/x-python", ".js": "text/javascript", ".ts": "text/typescript",
        ".xml": "application/xml", ".yaml": "application/x-yaml", ".yml": "application/x-yaml",
    }
    mime_type = mime_map.get(ext, "application/octet-stream")

    return ConnectorFileMetadata(
        external_id=f"s3://{bucket}/{key}",
        name=name,
        mime_type=mime_type,
        size_bytes=size,
        external_path=f"/{bucket}/{key}",
        raw_metadata={
            "provider": "s3",
            "bucket": bucket,
            "key": key,
            "etag": etag,
            "last_modified": last_modified,
        }
    )


def map_s3_event(event_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse a single S3 Event Notification record (from SQS/SNS/Lambda).
    Returns a dict with action ('put'|'delete') and the object key.
    """
    event_name = event_record.get("eventName", "")
    s3_info = event_record.get("s3", {})
    bucket = s3_info.get("bucket", {}).get("name", "")
    key = s3_info.get("object", {}).get("key", "").replace("+", " ")
    size = s3_info.get("object", {}).get("size", 0)
    etag = s3_info.get("object", {}).get("eTag", "")

    action = "delete" if event_name.startswith("ObjectRemoved") else "put"

    return {
        "action": action,
        "bucket": bucket,
        "key": key,
        "size": size,
        "etag": etag,
    }
