"""
db/engine.py

Async SQLAlchemy engine, session factory, and FastAPI dependency.

Usage (routes/services):
    from db.engine import get_db
    from sqlalchemy.ext.asyncio import AsyncSession

    async def my_handler(db: AsyncSession = Depends(get_db)):
        ...
"""

from __future__ import annotations

import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings

logger = logging.getLogger(__name__)


def _build_db_url() -> str:
    cfg = get_settings()
    db = cfg.database
    return (
        f"postgresql+asyncpg://{db.user}:{db.password}"
        f"@{db.host}:{db.port}/{db.name}"
    )


# Module-level engine — created once per process.
async_engine = create_async_engine(
    _build_db_url(),
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an ``AsyncSession`` per request.

    Commits on success, rolls back on exception, always closes.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
