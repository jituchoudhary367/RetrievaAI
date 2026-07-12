import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from connectors.health import HealthMonitor
from db.models.connector import Connector, ConnectorSyncState, ConnectorCredential, ConnectorHealth, ConnectorFile

@pytest.fixture
def mock_db():
    with patch("connectors.health._get_sync_db") as mock_get_db:
        mock_engine = MagicMock()
        mock_session = MagicMock()
        mock_get_db.return_value = (mock_engine, mock_session)
        yield mock_session

def test_health_monitor_healthy(mock_db):
    connector = Connector(id="123", status="connected")
    connector.credential = ConnectorCredential(expires_at=datetime.now(timezone.utc) + timedelta(minutes=60))
    connector.sync_state = ConnectorSyncState(webhook_channel_id="webhook-123")
    
    mock_db.get.return_value = connector
    
    # Mock counts (synced vs failed files)
    mock_db.execute.return_value.scalar.side_effect = [0, 50] # 0 failed, 50 synced
    
    result = HealthMonitor.check("123")
    
    assert result["overall_status"] == "healthy"
    assert result["oauth_expiry_minutes"] >= 59
    assert result["webhook_status"] == "active"
    assert result["failed_files"] == 0
    assert result["synced_files"] == 50
    assert mock_db.add.called

def test_health_monitor_unhealthy_expired(mock_db):
    connector = Connector(id="123", status="connected")
    connector.credential = ConnectorCredential(expires_at=datetime.now(timezone.utc) - timedelta(minutes=10))
    
    mock_db.get.return_value = connector
    mock_db.execute.return_value.scalar.side_effect = [0, 50]
    
    result = HealthMonitor.check("123")
    
    assert result["overall_status"] == "unhealthy"
    assert result["oauth_expiry_minutes"] <= -9
    assert result["webhook_status"] == "inactive"
