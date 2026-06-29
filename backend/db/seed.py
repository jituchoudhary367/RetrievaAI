"""
db/seed.py

Seeds the database with initial data that must exist before the app
can serve real traffic:
  1. Default tenant ("default")
  2. Three built-in Tool rows (vector_search, web_search, code_search)

Called once on startup in app/main.py (idempotent — skips if already seeded).
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.tenant import Tenant
from db.models.tool import Tool

logger = logging.getLogger(__name__)

_DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000001"
_DEFAULT_TENANT_SLUG = "default"

_BUILTIN_TOOLS = [
    {
        "id": "00000000-0000-0000-0001-000000000001",
        "name": "vector_search",
        "category": "retrieval",
        "description": (
            "Hybrid dense+sparse (BM25) vector search over the knowledge base. "
            "Returns relevant document chunks using Reciprocal Rank Fusion."
        ),
        "status": "active",
        "is_executable": True,
        "tenant_id": _DEFAULT_TENANT_ID,
    },
    {
        "id": "00000000-0000-0000-0001-000000000002",
        "name": "web_search",
        "category": "web",
        "description": (
            "Web search via Serper or Tavily API. "
            "Used by CRAG as a fallback when knowledge base results are insufficient."
        ),
        "status": "active",
        "is_executable": True,
        "tenant_id": _DEFAULT_TENANT_ID,
    },
    {
        "id": "00000000-0000-0000-0001-000000000003",
        "name": "code_search",
        "category": "code",
        "description": (
            "AST-based Python symbol and text search across the repository. "
            "Returns function/class definitions and text matches."
        ),
        "status": "active",
        "is_executable": True,
        "tenant_id": _DEFAULT_TENANT_ID,
    },
]


async def seed_database(db: AsyncSession) -> None:
    """Idempotently seed the database. Called once per startup."""
    await _seed_default_tenant(db)
    await _seed_builtin_tools(db)
    await db.commit()
    logger.info("Database seeding complete.")


async def _seed_default_tenant(db: AsyncSession) -> None:
    result = await db.execute(select(Tenant).where(Tenant.id == _DEFAULT_TENANT_ID))
    if result.scalar_one_or_none() is not None:
        return  # Already seeded

    tenant = Tenant(
        id=_DEFAULT_TENANT_ID,
        name="Default",
        slug=_DEFAULT_TENANT_SLUG,
        is_active=True,
        plan="free",
    )
    db.add(tenant)
    logger.info("Seeded default tenant.")


async def _seed_builtin_tools(db: AsyncSession) -> None:
    for t in _BUILTIN_TOOLS:
        result = await db.execute(select(Tool).where(Tool.id == t["id"]))
        if result.scalar_one_or_none() is not None:
            continue
        db.add(Tool(**t))
    logger.info("Seeded %d built-in tools.", len(_BUILTIN_TOOLS))


# Make the default tenant ID available to other modules
DEFAULT_TENANT_ID = _DEFAULT_TENANT_ID
