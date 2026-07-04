"""
routes/ingest.py

FastAPI router for triggering the ingestion pipeline over HTTP.

Endpoints:
  POST /api/v1/ingest  — Ingest files from a specified directory
  POST /api/v1/ingest/status — (Optional) check status if ingestion were async

Currently ingestion is blocking. In a heavy production system this would
dispatch to a Celery worker.
"""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
import tempfile
import os
from pydantic import BaseModel, Field

from pipeline.ingest import IngestionPipeline, IngestionReport

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest", tags=["ingest"])


class IngestRequest(BaseModel):
    """Payload for triggering an ingestion job."""
    path: str = Field(..., description="Absolute or relative path to a directory or file.")
    glob_pattern: str = Field(default="**/*", description="Glob pattern to filter files.")
    force: bool = Field(default=False, description="Bypass idempotency cache and force re-ingestion.")


# Dependency to get pipeline instance
def get_ingestion_pipeline() -> IngestionPipeline:
    return IngestionPipeline()


@router.post(
    "",
    response_model=IngestionReport,
    summary="Trigger ingestion pipeline on a directory or file",
)
def run_ingestion(
    request: IngestRequest,
    pipeline: IngestionPipeline = Depends(get_ingestion_pipeline),
) -> IngestionReport:
    """
    Run the ingestion pipeline on the specified path.

    Note: This is currently a blocking call.
    """
    target_path = Path(request.path)
    if not target_path.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Path does not exist: {request.path}"
        )

    logger.info("Received ingestion request for path %s (force=%s)", request.path, request.force)
    try:
        report = pipeline.ingest_path(
            path=target_path,
            glob=request.glob_pattern,
            force=request.force,
        )
        return report
    except Exception as exc:
        logger.error("Ingestion failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post(
    "/upload",
    response_model=IngestionReport,
    summary="Upload and ingest a file",
)
async def upload_and_ingest(
    file: UploadFile = File(...),
    pipeline: IngestionPipeline = Depends(get_ingestion_pipeline),
) -> IngestionReport:
    """
    Upload a file from the frontend, save it to a temporary location, 
    and run the ingestion pipeline on it.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
        
    try:
        # Create a temporary file with the original extension
        file_ext = Path(file.filename).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            tmp_path = Path(tmp_file.name)
            
            # Read and write chunks
            while content := await file.read(1024 * 1024):  # 1MB chunks
                tmp_file.write(content)
        
        logger.info("Received file upload: %s, saved to %s", file.filename, tmp_path)

        # Run ingestion
        report = pipeline.ingest_path(tmp_path, force=True) 

        # Delete the temp file after ingestion
        try:
            os.remove(tmp_path)
            logger.info("Cleaned up temp file: %s", tmp_path)
        except Exception as e:
            logger.warning("Failed to clean up temp file %s: %s", tmp_path, e)

        # Overwrite the path in the report with the original filename for the frontend
        for result in report.results:
            result.path = file.filename

        return report

    except Exception as exc:
        logger.error("Error during file upload/ingest: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


__all__ = ["router"]
