import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from connectors.orchestrator import ConnectorOrchestrator
from connectors.registry import ConnectorRegistry
from connectors.base.connector import BaseConnector
from connectors.base.capabilities import CapabilitySet, Capability
from connectors.base.metadata import ConnectorFileMetadata
from connectors.models import FileChange, FileChangeType
from db.models.connector import Connector, ConnectorSyncState, ConnectorFile
from typing import AsyncIterator, Dict, Any, List
from connectors.base.sync import SyncCursor

class MockAdapter(BaseConnector):
    @property
    def provider_name(self) -> str:
        return "mock_provider"
    
    def capabilities(self) -> CapabilitySet:
        return {Capability.INCREMENTAL_SYNC}

    async def authenticate(self, credentials: Dict[str, Any]) -> None:
        pass
    async def refresh_token(self) -> None:
        pass
    async def health_check(self) -> Dict[str, Any]:
        return {}
    async def full_sync(self) -> AsyncIterator[ConnectorFileMetadata]:
        yield ConnectorFileMetadata(external_id="file1", name="file1.txt")
        yield ConnectorFileMetadata(external_id="file2", name="file2.txt")
    async def incremental_sync(self, cursor: SyncCursor) -> AsyncIterator[FileChange]:
        yield FileChange(file_id="file3", change_type=FileChangeType.MODIFIED, file_metadata=ConnectorFileMetadata(external_id="file3", name="file3.txt"))
        yield FileChange(file_id="file1", change_type=FileChangeType.DELETED)
    async def download_file(self, external_id: str) -> bytes:
        return b"test content"
    async def detect_deletes(self, known_ids: List[str]) -> List[str]:
        return []

    async def get_permissions(self) -> List[Any]:
        return []

@pytest.fixture(autouse=True)
def setup_registry():
    ConnectorRegistry.clear()
    ConnectorRegistry.register("mock_provider", MockAdapter)
    yield
    ConnectorRegistry.clear()

@pytest.fixture
def db_session_mock():
    session = MagicMock()
    # Return nothing when checking for existing files
    session.query.return_value.filter_by.return_value.first.return_value = None
    return session

@pytest.fixture
def connector_mock():
    conn = Connector(id="conn1", provider="mock_provider", user_id="user1")
    conn.sync_state = ConnectorSyncState()
    return conn

@patch("connectors.tasks.download_and_enqueue_task")
def test_run_full_sync(mock_enqueue, db_session_mock, connector_mock):
    ConnectorOrchestrator.run_full_sync(db_session_mock, connector_mock, "dummy_token")
    
    # 2 files yielded by mock adapter
    assert mock_enqueue.delay.call_count == 2
    
    # Check what was queued
    calls = mock_enqueue.delay.call_args_list
    assert calls[0].kwargs["remote_file_id"] == "file1"
    assert calls[1].kwargs["remote_file_id"] == "file2"
    
    assert connector_mock.status == "connected"
    assert connector_mock.sync_state.last_sync_status == "completed"

@patch("connectors.tasks.download_and_enqueue_task")
def test_run_incremental_sync(mock_enqueue, db_session_mock, connector_mock):
    # Setup mock to return a file row for deletion
    mock_file_row = MagicMock()
    db_session_mock.query.return_value.filter_by.return_value.first.side_effect = [None, mock_file_row]

    ConnectorOrchestrator.run_incremental_sync(db_session_mock, connector_mock, "dummy_token")
    
    # 1 modification, 1 deletion
    # So 1 dispatch
    assert mock_enqueue.delay.call_count == 1
    calls = mock_enqueue.delay.call_args_list
    assert calls[0].kwargs["remote_file_id"] == "file3"
    
    # The deleted file should have its status updated to deleted
    assert mock_file_row.sync_status == "deleted"
