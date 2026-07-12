import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from db.models.connector import Connector, ConnectorSyncState, ConnectorCredential
from connectors.models import ConnectorStatusEnum
import uuid

@pytest.fixture
def mock_db_session():
    mock_db = AsyncMock()
    mock_execute_result = MagicMock()
    mock_connector = Connector(
        id="123",
        user_id="test_user",
        provider="google_drive",
        status="connected",
        auto_sync=True
    )
    mock_execute_result.scalar_one_or_none.return_value = mock_connector
    mock_db.execute.return_value = mock_execute_result
    return mock_db

@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = "test_user"
    return user

@pytest.mark.asyncio
async def test_pause_connector():
    with patch("services.connector_service.pause_connector", new_callable=AsyncMock) as mock_svc_pause:
        mock_svc_pause.return_value = True
        
        # Test directly via the router since we are using FastAPI
        from routes.connectors import pause_connector
        
        db = AsyncMock()
        user = MagicMock()
        user.id = "test_user"
        
        result = await pause_connector("123", user, db)
        assert result == {"status": "paused"}
        mock_svc_pause.assert_called_once_with(db, "test_user", "123")

@pytest.mark.asyncio
async def test_resume_connector():
    with patch("services.connector_service.resume_connector", new_callable=AsyncMock) as mock_svc_resume:
        mock_svc_resume.return_value = True
        
        from routes.connectors import resume_connector
        
        db = AsyncMock()
        user = MagicMock()
        user.id = "test_user"
        
        result = await resume_connector("123", user, db)
        assert result == {"status": "resumed"}
        mock_svc_resume.assert_called_once_with(db, "test_user", "123")
