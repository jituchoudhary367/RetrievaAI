"""
routes/tools.py

Tool registry endpoints (§1.5).

Endpoints:
  GET    /api/tools
  GET    /api/tools/{id}
  GET    /api/tools/{id}/executions
  POST   /api/tools                 (Register metadata-only tools)
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.engine import get_db
from db.models.tool import Tool, ToolExecution
from security.auth import get_current_user, require_role
from services.audit import log_action
from db.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tools", tags=["tools"])

# ── Response schemas ─────────────────────────────────────────────────────

class ToolOut(BaseModel):
    id: str
    name: str
    category: str
    description: Optional[str]
    status: str
    is_executable: bool
    created_at: str

    @classmethod
    def from_orm(cls, t: Tool) -> "ToolOut":
        return cls(
            id=t.id,
            name=t.name,
            category=t.category,
            description=t.description,
            status=t.status,
            is_executable=t.is_executable,
            created_at=t.created_at.isoformat(),
        )

class ToolExecutionOut(BaseModel):
    id: str
    status: str
    latency_ms: Optional[float]
    error_message: Optional[str]
    created_at: str

    @classmethod
    def from_orm(cls, te: ToolExecution) -> "ToolExecutionOut":
        return cls(
            id=te.id,
            status=te.status,
            latency_ms=te.latency_ms,
            error_message=te.error_message,
            created_at=te.created_at.isoformat(),
        )

class RegisterToolRequest(BaseModel):
    name: str
    category: str
    description: Optional[str] = None


# ── Routes ───────────────────────────────────────────────────────────────

@router.get("", response_model=List[ToolOut])
async def list_tools(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ToolOut]:
    result = await db.execute(
        select(Tool).order_by(Tool.name)
    )
    tools = result.scalars().all()
    return [ToolOut.from_orm(t) for t in tools]

@router.post("", response_model=ToolOut, status_code=201)
async def register_tool(
    body: RegisterToolRequest,
    current_user: User = Depends(require_role("TENANT_ADMIN", "EDITOR")),
    db: AsyncSession = Depends(get_db),
) -> ToolOut:
    """Register a new metadata-only tool."""
    tool = Tool(
        name=body.name,
        category=body.category,
        description=body.description,
        status="active",
        is_executable=False, # User registered tools are not executable by the backend CRAG currently
    )
    db.add(tool)
    await db.flush()
    await db.commit()
    
    import asyncio
    asyncio.create_task(log_action(
        actor_user_id=current_user.id,
        action="tool.register",
        target=f"tool:{tool.id}",
        detail={"name": tool.name},
    ))
    
    return ToolOut.from_orm(tool)

@router.get("/{tool_id}", response_model=ToolOut)
async def get_tool(
    tool_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ToolOut:
    result = await db.execute(
        select(Tool).where(Tool.id == tool_id)
    )
    tool = result.scalar_one_or_none()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return ToolOut.from_orm(tool)

@router.get("/{tool_id}/executions", response_model=List[ToolExecutionOut])
async def get_tool_executions(
    tool_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ToolExecutionOut]:
    # Verify tool exists for tenant
    tool = await db.execute(
        select(Tool.id).where(Tool.id == tool_id)
    )
    if not tool.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Tool not found")
        
    result = await db.execute(
        select(ToolExecution)
        .where(ToolExecution.tool_id == tool_id)
        .order_by(ToolExecution.created_at.desc())
        .limit(limit)
    )
    executions = result.scalars().all()
    return [ToolExecutionOut.from_orm(e) for e in executions]
