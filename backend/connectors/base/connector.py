from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Dict, Optional, Any
from .metadata import ConnectorFileMetadata, ConnectorPermission
from .sync import SyncResult, SyncCursor
from .capabilities import CapabilitySet

class BaseConnector(ABC):
    """
    Abstract interface all connectors must implement.
    Every provider adapter implements only this class.
    """
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique provider identifier, e.g. 'google_drive'."""
        pass

    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def refresh_token(self) -> None:
        pass

    @abstractmethod
    def capabilities(self) -> CapabilitySet:
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def full_sync(self) -> AsyncIterator[ConnectorFileMetadata]:
        pass

    @abstractmethod
    async def incremental_sync(self, cursor: SyncCursor) -> AsyncIterator[ConnectorFileMetadata]:
        pass

    @abstractmethod
    async def download_file(self, external_id: str) -> bytes:
        pass

    @abstractmethod
    async def detect_deletes(self, known_ids: List[str]) -> List[str]:
        pass

    @abstractmethod
    async def get_permissions(self, external_id: str) -> List[ConnectorPermission]:
        pass

    async def register_webhook(self, callback_url: str) -> Optional[Dict[str, Any]]:
        """Optional — connectors without webhook support return None."""
        return None
