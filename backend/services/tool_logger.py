"""
services/tool_logger.py

Tool Execution logger (§1.5).

Fire-and-forget logging of tool executions to the `tool_executions` Postgres table.
Used by CRAG and the search API to record every tool invocation.
"""

from __future__ import annotations

import logging
from typing import Optional

from db.engine import async_session_factory
from db.models.tool import ToolExecution

logger = logging.getLogger(__name__)

async def log_tool_execution(
    *,
    tenant_id: str,
    tool_id: str,
    status: str,  # "success" or "failed"
    latency_ms: Optional[float] = None,
    error_message: Optional[str] = None,
) -> None:
    """Write a ToolExecution row."""
    try:
        async with async_session_factory() as db:
            db.add(ToolExecution(
                tenant_id=tenant_id,
                tool_id=tool_id,
                status=status,
                latency_ms=latency_ms,
                error_message=error_message,
            ))
            await db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("ToolLogger: failed to write ToolExecution: %s", exc)

__all__ = ["log_tool_execution"]
