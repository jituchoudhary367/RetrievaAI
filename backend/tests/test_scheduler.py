import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from connectors.scheduler import _process_connector
from db.models.connector import Connector, ConnectorSyncState, ConnectorCredential

def test_process_connector_needs_sync_no_state():
    connector = Connector(id="123", sync_interval_minutes=60)
    # No sync_state => should trigger sync
    
    with patch("connectors.scheduler.discover_files_task.delay") as mock_delay:
        _process_connector(connector, datetime.now(timezone.utc))
        mock_delay.assert_called_once_with("123", is_incremental=True)

def test_process_connector_needs_sync_interval_elapsed():
    now = datetime.now(timezone.utc)
    last_sync = now - timedelta(minutes=61)
    
    sync_state = ConnectorSyncState(last_sync_completed_at=last_sync)
    connector = Connector(id="123", sync_interval_minutes=60)
    connector.sync_state = sync_state
    
    with patch("connectors.scheduler.discover_files_task.delay") as mock_delay:
        _process_connector(connector, now)
        mock_delay.assert_called_once_with("123", is_incremental=True)

def test_process_connector_no_sync_needed():
    now = datetime.now(timezone.utc)
    last_sync = now - timedelta(minutes=10) # Less than interval
    
    sync_state = ConnectorSyncState(last_sync_completed_at=last_sync)
    connector = Connector(id="123", sync_interval_minutes=60)
    connector.sync_state = sync_state
    
    with patch("connectors.scheduler.discover_files_task.delay") as mock_delay:
        _process_connector(connector, now)
        mock_delay.assert_not_called()

def test_process_connector_needs_token_refresh():
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=10) # Less than 15 minutes away
    
    sync_state = ConnectorSyncState(last_sync_completed_at=now) # No sync needed
    credential = ConnectorCredential(expires_at=expires_at, refresh_token="dummy")
    
    connector = Connector(id="123", sync_interval_minutes=60)
    connector.sync_state = sync_state
    connector.credential = credential
    
    with patch("connectors.scheduler.refresh_token_task.delay") as mock_delay:
        _process_connector(connector, now)
        mock_delay.assert_called_once_with("123")
