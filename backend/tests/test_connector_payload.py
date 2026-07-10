import pytest
from connectors.base.payload import IngestionTaskPayload

def test_ingestion_task_payload_instantiation():
    payload = IngestionTaskPayload(
        connector_id="conn-123",
        connector_file_id="file-123",
        external_id="ext-123",
        org_id="org-123",
        source_provider="google_drive",
        file_bytes_ref="path/to/temp/blob",
        original_filename="document.pdf",
        mime_type="application/pdf",
        metadata={"title": "Important Document"}
    )
    
    assert payload.connector_id == "conn-123"
    assert payload.external_id == "ext-123"
    assert payload.source_provider == "google_drive"
    assert payload.file_bytes_ref == "path/to/temp/blob"
    assert payload.metadata["title"] == "Important Document"
    
def test_payload_to_dict_matches_downstream_expectations():
    """
    Ensures that the IngestionTaskPayload serializes to a dict
    that downstream tasks (like existing Celery tasks) can consume.
    """
    payload = IngestionTaskPayload(
        connector_id="conn-123",
        connector_file_id="file-123",
        external_id="ext-123",
        org_id="org-123",
        source_provider="google_drive",
        file_bytes_ref="blob:1234",
        original_filename="doc.txt",
    )
    
    # We can pass this model dump to a generic task that expects these kwargs
    dump = payload.model_dump()
    assert dump["connector_id"] == "conn-123"
    assert dump["original_filename"] == "doc.txt"
    assert dump["metadata"] == {} # default
