from enum import Enum
from typing import Optional
from pydantic import BaseModel

class SyncMode(str, Enum):
    FULL = "full"
    INCREMENTAL = "incremental"

class SyncCursor(BaseModel):
    """
    Opaque token or watermark used for incremental syncs.
    """
    token: Optional[str] = None

class SyncResult(BaseModel):
    """
    Result of a synchronization operation.
    """
    successful: bool
    files_discovered: int = 0
    files_failed: int = 0
    next_cursor: Optional[SyncCursor] = None
    error_message: Optional[str] = None
