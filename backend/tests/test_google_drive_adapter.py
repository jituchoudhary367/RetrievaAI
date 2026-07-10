import pytest
from unittest.mock import AsyncMock, MagicMock
from connectors.google_drive.adapter import GoogleDriveConnector
from connectors.models import FileListResult, FileMetadata, ChangeList, FileChange, FileChangeType

@pytest.fixture
def mock_drive_client(monkeypatch):
    client_mock = AsyncMock()
    monkeypatch.setattr("connectors.google_drive.adapter.GoogleDriveClient", lambda *args, **kwargs: client_mock)
    return client_mock

@pytest.mark.asyncio
async def test_adapter_authenticate():
    adapter = GoogleDriveConnector()
    await adapter.authenticate({"access_token": "test-token", "refresh_token": "refresh-token"})
    assert adapter._access_token == "test-token"
    assert adapter._refresh_token == "refresh-token"

@pytest.mark.asyncio
async def test_adapter_full_sync(mock_drive_client):
    adapter = GoogleDriveConnector()
    await adapter.authenticate({"access_token": "test-token"})
    
    mock_drive_client.list_files.return_value = FileListResult(
        files=[
            FileMetadata(file_id="123", name="test.txt", mime_type="text/plain", size_bytes=100)
        ],
        next_page_token=None,
        has_more=False
    )
    
    files = []
    async for f in adapter.full_sync():
        files.append(f)
        
    assert len(files) == 1
    assert files[0].external_id == "123"
    assert files[0].name == "test.txt"
    assert files[0].size_bytes == 100

@pytest.mark.asyncio
async def test_adapter_incremental_sync(mock_drive_client):
    adapter = GoogleDriveConnector()
    await adapter.authenticate({"access_token": "test-token"})
    
    from connectors.base.sync import SyncCursor
    
    mock_drive_client.get_changes.return_value = ChangeList(
        changes=[
            FileChange(file_id="123", change_type=FileChangeType.MODIFIED, file_metadata=FileMetadata(file_id="123", name="test2.txt", mime_type="text/plain", size_bytes=200))
        ],
        new_change_token=None,
        has_more=False
    )
    
    files = []
    async for f in adapter.incremental_sync(SyncCursor(token="token1")):
        files.append(f)
        
    assert len(files) == 1
    assert files[0].external_id == "123"
    assert files[0].name == "test2.txt"

@pytest.mark.asyncio
async def test_adapter_health_check_success(mock_drive_client):
    adapter = GoogleDriveConnector()
    await adapter.authenticate({"access_token": "test-token"})
    mock_drive_client.list_files.return_value = FileListResult(files=[], next_page_token=None, has_more=False)
    
    res = await adapter.health_check()
    assert res["status"] == "ok"
