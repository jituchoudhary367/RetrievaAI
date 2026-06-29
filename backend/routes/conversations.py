"""
routes/conversations.py

Conversations API — fetching persisted chat history (§1.10).

Endpoints:
  GET /api/conversations
  GET /api/conversations/{id}/messages
"""

from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.engine import get_db
from db.models.conversation import Conversation, ConversationMessage
from security.auth import get_current_user
from db.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/conversations", tags=["conversations"])

# ── Response schemas ─────────────────────────────────────────────────────

class ConversationOut(BaseModel):
    id: str
    session_id: str
    title: str | None
    created_at: str
    updated_at: str

    @classmethod
    def from_orm(cls, c: Conversation) -> "ConversationOut":
        return cls(
            id=c.id,
            session_id=c.session_id,
            title=c.title,
            created_at=c.created_at.isoformat(),
            updated_at=c.updated_at.isoformat(),
        )

class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    created_at: str

    @classmethod
    def from_orm(cls, m: ConversationMessage) -> "MessageOut":
        return cls(
            id=m.id,
            role=m.role,
            content=m.content,
            created_at=m.created_at.isoformat(),
        )

# ── Routes ───────────────────────────────────────────────────────────────

@router.get("", response_model=List[ConversationOut])
async def list_conversations(
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ConversationOut]:
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .limit(limit)
    )
    conversations = result.scalars().all()
    return [ConversationOut.from_orm(c) for c in conversations]

@router.get("/{session_id}/messages", response_model=List[MessageOut])
async def get_conversation_messages(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[MessageOut]:
    result = await db.execute(
        select(Conversation)
        .where(Conversation.session_id == session_id, Conversation.user_id == current_user.id)
        .options(selectinload(Conversation.messages))
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        # It's possible the conversation is purely in Redis and hasn't been flushed yet,
        # or doesn't exist. We just return empty list.
        return []
    
    return [MessageOut.from_orm(m) for m in conversation.messages]
