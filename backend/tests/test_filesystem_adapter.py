import os
import pytest
import tempfile
from unittest.mock import MagicMock, patch

from connectors.filesystem.mapper import (
    map_filesystem_file,
    map_filesystem_event,
    is_indexable,
    compute_checksum
)
from connectors.filesystem.adapter import FilesystemAdapter

def test_is_indexable():
    assert is_indexable("file.txt") is True
    assert is_indexable("image.png") is False
    assert is_indexable("app.exe") is False

def test_compute_checksum():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"hello world")
        temp_path = f.name
    
    try:
        checksum = compute_checksum(temp_path)
        # sha256 of "hello world"
        assert checksum == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    finally:
        os.remove(temp_path)

def test_map_filesystem_file():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".md") as f:
        f.write(b"hello world")
        temp_path = f.name
        
    root_dir = os.path.dirname(temp_path)
    
    try:
        metadata = map_filesystem_file(temp_path, root_dir)
        assert metadata.external_id == "fs://b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
        assert metadata.mime_type == "text/markdown"
        assert metadata.size_bytes == 11
        assert metadata.raw_metadata["provider"] == "filesystem"
    finally:
        os.remove(temp_path)

def test_map_filesystem_event_move():
    event = map_filesystem_event("moved", "old.txt", "new.txt")
    assert event["action"] == "put"
    assert event["src_path"] == "old.txt"
    assert event["dest_path"] == "new.txt"

def test_map_filesystem_event_delete():
    event = map_filesystem_event("deleted", "old.txt")
    assert event["action"] == "delete"

@pytest.mark.asyncio
async def test_adapter_process_watchdog_event_put():
    adapter = FilesystemAdapter()
    
    with tempfile.TemporaryDirectory() as root_dir:
        await adapter.authenticate({"root_dir": root_dir})
        
        file_path = os.path.join(root_dir, "test.txt")
        with open(file_path, "wb") as f:
            f.write(b"content")
            
        metadata = adapter.process_watchdog_event("created", file_path)
        assert metadata is not None
        assert metadata.external_id.startswith("fs://")
        
        # Verify cache was updated
        checksum = metadata.external_id[5:]
        assert adapter._checksum_cache[checksum] == file_path

@pytest.mark.asyncio
async def test_adapter_process_watchdog_event_rename():
    adapter = FilesystemAdapter()
    
    with tempfile.TemporaryDirectory() as root_dir:
        await adapter.authenticate({"root_dir": root_dir})
        
        # Create file at A
        file_a = os.path.join(root_dir, "a.txt")
        with open(file_a, "wb") as f:
            f.write(b"content")
            
        meta_a = adapter.process_watchdog_event("created", file_a)
        
        # Move A to B
        file_b = os.path.join(root_dir, "b.txt")
        os.rename(file_a, file_b)
        
        meta_b = adapter.process_watchdog_event("moved", file_a, file_b)
        
        # The external ID (checksum) MUST be identical
        assert meta_a.external_id == meta_b.external_id
        
        # But the path in metadata must be updated
        assert meta_b.external_path == file_b

@pytest.mark.asyncio
async def test_adapter_process_watchdog_event_delete():
    adapter = FilesystemAdapter()
    
    with tempfile.TemporaryDirectory() as root_dir:
        await adapter.authenticate({"root_dir": root_dir})
        
        # It should return None for deletes so caller can tombstone
        result = adapter.process_watchdog_event("deleted", os.path.join(root_dir, "gone.txt"))
        assert result is None
