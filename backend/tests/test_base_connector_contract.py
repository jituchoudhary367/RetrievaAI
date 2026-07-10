import pytest
from typing import AsyncIterator, List, Dict, Any, Optional
from connectors.base.connector import BaseConnector
from connectors.base.metadata import ConnectorFileMetadata, ConnectorPermission
from connectors.base.capabilities import CapabilitySet, Capability
from connectors.base.sync import SyncCursor

class DummyConnector(BaseConnector):
    @property
    def provider_name(self) -> str:
        return "dummy"

    async def authenticate(self, credentials: Dict[str, Any]) -> None:
        pass

    async def refresh_token(self) -> None:
        pass

    def capabilities(self) -> CapabilitySet:
        return {Capability.OAUTH}

    async def health_check(self) -> Dict[str, Any]:
        return {"status": "ok"}

    async def full_sync(self) -> AsyncIterator[ConnectorFileMetadata]:
        yield ConnectorFileMetadata(external_id="1", name="test", mime_type="text/plain")

    async def incremental_sync(self, cursor: SyncCursor) -> AsyncIterator[ConnectorFileMetadata]:
        yield ConnectorFileMetadata(external_id="2", name="test2", mime_type="text/plain")

    async def download_file(self, external_id: str) -> bytes:
        return b"content"

    async def detect_deletes(self, known_ids: List[str]) -> List[str]:
        return []

    async def get_permissions(self, external_id: str) -> List[ConnectorPermission]:
        return []

def test_base_connector_cannot_be_instantiated():
    with pytest.raises(TypeError):
        BaseConnector() # type: ignore

def test_dummy_connector_can_be_instantiated():
    connector = DummyConnector()
    assert connector.provider_name == "dummy"
    assert Capability.OAUTH in connector.capabilities()
