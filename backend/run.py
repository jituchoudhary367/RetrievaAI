"""
run.py

Local development entry point.
Starts the Uvicorn ASGI server with hot-reload enabled.
"""

from __future__ import annotations

import uvicorn
from app.config import get_settings

def run() -> None:
    """Run the FastAPI server via Uvicorn."""
    settings = get_settings()
    # In a production environment, this is typically launched via
    # `uvicorn main:app --host 0.0.0.0 --port 8000` or Gunicorn.
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug,
        log_level=settings.observability.log_level.lower(),
    )

if __name__ == "__main__":
    run()
