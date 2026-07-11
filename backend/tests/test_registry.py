import pytest
from connectors.registry import ConnectorRegistry
from connectors.base.connector import BaseConnector
from typing import AsyncIterator, List, Dict, Any, Optional
from connectors.base.metadata import ConnectorFileMetadata, ConnectorPermission
from connectors.base.sync import SyncCursor
from connectors.base.capabilities import CapabilitySet, Capability

class DummyConnector(BaseConnector):
    @property
    def provider_name(self) -> str:
        return "dummy"
    
    def capabilities(self) -> CapabilitySet:
        return {Capability.OAUTH}

    async def authenticate(self, credentials: Dict[str, Any]) -> None:
        pass
    async def refresh_token(self) -> None:
        pass
    async def health_check(self) -> Dict[str, Any]:
        return {}
    async def full_sync(self) -> AsyncIterator[ConnectorFileMetadata]:
        yield ConnectorFileMetadata(external_id="1", name="1")
    async def incremental_sync(self, cursor: SyncCursor) -> AsyncIterator[ConnectorFileMetadata]:
        yield ConnectorFileMetadata(external_id="1", name="1")
    async def download_file(self, external_id: str) -> bytes:
        return b""
    async def detect_deletes(self, known_ids: List[str]) -> List[str]:
        return []
    async def get_permissions(self, external_id: str) -> List[ConnectorPermission]:
        return []

@pytest.fixture(autouse=True)
def cleanup_registry():
    ConnectorRegistry.clear()
    yield
    ConnectorRegistry.clear()

def test_registry_register_and_get():
    ConnectorRegistry.register("dummy", DummyConnector, version="1.5.0")
    
    cls = ConnectorRegistry.get("dummy")
    assert cls is DummyConnector
    
    caps = ConnectorRegistry.capabilities_of("dummy")
    assert Capability.OAUTH in caps

def test_registry_duplicate_registration_fails():
    ConnectorRegistry.register("dummy", DummyConnector)
    with pytest.raises(ValueError, match="already registered"):
        ConnectorRegistry.register("dummy", DummyConnector)

def test_registry_missing_provider_fails():
    with pytest.raises(KeyError, match="Unknown connector"):
        ConnectorRegistry.get("nonexistent")

def test_registry_enable_disable():
    ConnectorRegistry.register("dummy", DummyConnector)
    
    assert "dummy" in ConnectorRegistry.list_active()
    
    ConnectorRegistry.disable("dummy")
    assert "dummy" not in ConnectorRegistry.list_active()
    
    ConnectorRegistry.enable("dummy")
    assert "dummy" in ConnectorRegistry.list_active()

def test_registry_autodiscover():
    # Since registry is cleared before test, we can just call autodiscover manually
    ConnectorRegistry.autodiscover()
    
    # We should have google_drive discovered
    active = ConnectorRegistry.list_active()
    assert "google_drive" in active
    
    caps = ConnectorRegistry.capabilities_of("google_drive")
    assert Capability.INCREMENTAL_SYNC in caps
    
    entry = ConnectorRegistry.get_entry("google_drive")
    assert entry.version == "1.0.0"
