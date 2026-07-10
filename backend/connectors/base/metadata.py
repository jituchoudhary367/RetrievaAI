from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class ConnectorPermission(BaseModel):
    """
    Represents a unified access control rule from a source system.
    """
    principal_type: str  # user, group, domain, anyone
    principal_id: str
    role: str            # owner, editor, viewer, commenter

class ConnectorFileMetadata(BaseModel):
    """
    Represents a normalized document/file discovered in a source system.
    """
    external_id: str
    external_path: Optional[str] = None
    name: str
    mime_type: Optional[str] = None
    checksum: Optional[str] = None
    size_bytes: Optional[int] = None
    raw_metadata: Dict[str, Any] = {}
    permissions: List[ConnectorPermission] = []
