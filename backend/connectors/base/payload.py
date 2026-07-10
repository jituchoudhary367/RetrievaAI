from pydantic import BaseModel
from typing import Optional, Dict, Any

class IngestionTaskPayload(BaseModel):
    """
    The strict boundary contract ("the seam") bridging the connector
    framework into the existing ingestion orchestrator/Celery tasks.
    """
    connector_id: str
    connector_file_id: str
    external_id: str
    org_id: str
    source_provider: str
    file_bytes_ref: str        # pointer to temp storage/blob, not raw bytes in Celery payload
    original_filename: str
    mime_type: Optional[str] = None
    metadata: Dict[str, Any] = {}
