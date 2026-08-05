import pytest
import sqlite3
import tempfile
import os
from sqlalchemy import text
from unittest.mock import MagicMock
from connectors.database.mapper import map_database_row, render_row_to_markdown
from connectors.database.adapter import DatabaseAdapter
from connectors.base.sync import SyncCursor

def test_render_row_to_markdown_template():
    row = {"id": 1, "title": "Help", "desc": "Login issue"}
    config = {"content_template": "# {title}\n\n{desc}"}
    md = render_row_to_markdown(row, config)
    assert md == "# Help\n\nLogin issue"

def test_render_row_to_markdown_columns():
    row = {"id": 1, "status": "Open", "priority": "High"}
    config = {"content_columns": ["status", "priority"]}
    md = render_row_to_markdown(row, config)
    assert "**status**: Open" in md
    assert "**priority**: High" in md

def test_map_database_row():
    row = {"id": 123, "subject": "Test"}
    config = {"title_template": "Ticket {id} - {subject}"}
    cf = map_database_row(row, "tickets", "id", config)
    
    assert cf.external_id == "db://tickets/123"
    assert cf.name == "Ticket 123 - Test.md"
    assert cf.mime_type == "text/markdown"
    assert cf.raw_metadata["row_data"] == row

@pytest.fixture
def sqlite_db_url():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield f"sqlite:///{path}"
    if os.path.exists(path):
        os.remove(path)

@pytest.mark.asyncio
async def test_adapter_full_sync(sqlite_db_url):
    adapter = DatabaseAdapter()
    await adapter.authenticate({
        "connection_string": sqlite_db_url,
        "table_name": "tickets",
        "pk_column": "id",
    })
    
    with adapter._engine.begin() as conn:
        conn.execute(text("CREATE TABLE tickets (id INTEGER PRIMARY KEY, updated_at TEXT, subject TEXT)"))
        conn.execute(text("INSERT INTO tickets VALUES (1, '2024-01-01', 'First')"))
        conn.execute(text("INSERT INTO tickets VALUES (2, '2024-01-02', 'Second')"))
    
    items = []
    async for item in adapter.full_sync():
        items.append(item)
        
    assert len(items) == 2
    assert items[0].external_id == "db://tickets/1"
    assert items[1].external_id == "db://tickets/2"
    adapter._engine.dispose()

@pytest.mark.asyncio
async def test_adapter_incremental_sync(sqlite_db_url):
    adapter = DatabaseAdapter()
    await adapter.authenticate({
        "connection_string": sqlite_db_url,
        "table_name": "tickets",
        "pk_column": "id",
        "watermark_column": "updated_at"
    })
    
    with adapter._engine.begin() as conn:
        conn.execute(text("CREATE TABLE tickets (id INTEGER PRIMARY KEY, updated_at TEXT, subject TEXT)"))
        conn.execute(text("INSERT INTO tickets VALUES (1, '2024-01-01', 'First')"))
        conn.execute(text("INSERT INTO tickets VALUES (2, '2024-01-02', 'Second')"))
        conn.execute(text("INSERT INTO tickets VALUES (3, '2024-01-03', 'Third')"))
    
    cursor = SyncCursor(token="2024-01-01")
    items = []
    async for item in adapter.incremental_sync(cursor):
        items.append(item)
        
    assert len(items) == 2
    assert items[0].external_id == "db://tickets/2"
    assert items[1].external_id == "db://tickets/3"
    
    # Cursor should be updated to the max watermark
    assert cursor.token == "2024-01-03"
    adapter._engine.dispose()

@pytest.mark.asyncio
async def test_adapter_download_file(sqlite_db_url):
    adapter = DatabaseAdapter()
    await adapter.authenticate({
        "connection_string": sqlite_db_url,
        "table_name": "tickets",
        "pk_column": "id",
        "mapping_config": {"content_template": "Subject: {subject}"}
    })
    
    with adapter._engine.begin() as conn:
        conn.execute(text("CREATE TABLE tickets (id INTEGER PRIMARY KEY, updated_at TEXT, subject TEXT)"))
        conn.execute(text("INSERT INTO tickets VALUES (1, '2024-01-01', 'First Ticket')"))
    
    content = await adapter.download_file("db://tickets/1")
    assert content.decode("utf-8") == "Subject: First Ticket"
    adapter._engine.dispose()
