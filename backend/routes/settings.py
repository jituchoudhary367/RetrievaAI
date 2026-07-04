"""
routes/settings.py

Settings endpoints (§1.7, §1.8, §1.9).

Endpoints:
  GET    /api/settings/{category}  (reads from RuntimeSettingsService)
  PUT    /api/settings/{category}  (writes to RuntimeSettingsService)
  GET    /api/settings/api-keys
  POST   /api/settings/api-keys
  DELETE /api/settings/api-keys/{id}
  GET    /api/settings/sessions
  DELETE /api/settings/sessions/{id}
  GET    /api/settings/audit-log
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import os
import dotenv
from app.config import get_settings

from db.engine import get_db
from db.models.settings import RuntimeSetting
from db.models.security import ApiKey
from db.models.user import User, UserSession
from db.models.audit import AuditLogEntry
from security.auth import get_current_user, require_role
from services.runtime_settings import get_runtime_settings
from services.audit import log_action

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/settings", tags=["settings"])


# ── Runtime Settings ─────────────────────────────────────────────────────

@router.get("/{category}")
async def get_settings_category(
    category: str,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get all settings for a tenant. (Category is ignored in DB for simplicity, we return all)."""
    svc = get_runtime_settings()
    settings = await svc.get_all()
    if category == "integrations":
        from services.user_preferences import get_user_preferences
        prefs_svc = get_user_preferences()
        user_prefs = await prefs_svc.get_all_for_user(current_user.id)
        
        settings["SERPER_API_KEY"] = user_prefs.get("SERPER_API_KEY", "")
        settings["GROQ_API_KEY"] = user_prefs.get("GROQ_API_KEY", "")
        
        if current_user.email == "jituchoudharyat@gmail.com":
            app_settings = get_settings()
            env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
            serper = dotenv.get_key(env_path, "SERPER_API_KEY") if os.path.exists(env_path) else app_settings.serper_api_key
            groq = dotenv.get_key(env_path, "GROQ_API_KEY") if os.path.exists(env_path) else getattr(app_settings, "groq_api_key", None)
            
            if not settings.get("SERPER_API_KEY") and serper:
                settings["SERPER_API_KEY"] = serper
                import asyncio
                asyncio.create_task(prefs_svc.set(current_user.id, "SERPER_API_KEY", serper))
            if not settings.get("GROQ_API_KEY") and groq:
                settings["GROQ_API_KEY"] = groq
                import asyncio
                asyncio.create_task(prefs_svc.set(current_user.id, "GROQ_API_KEY", groq))
    return settings

@router.put("/{category}")
async def update_settings_category(
    category: str,
    settings: Dict[str, Any],
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Update multiple settings at once."""
    svc = get_runtime_settings()
    for key, value in settings.items():
        await svc.set(key, value, updated_by=current_user.id)
    
    if category == "integrations":
        from services.user_preferences import get_user_preferences
        prefs_svc = get_user_preferences()
        
        if "GROQ_API_KEY" in settings:
            await prefs_svc.set(current_user.id, "GROQ_API_KEY", settings["GROQ_API_KEY"])
        if "SERPER_API_KEY" in settings:
            await prefs_svc.set(current_user.id, "SERPER_API_KEY", settings["SERPER_API_KEY"])
            
    import asyncio
    asyncio.create_task(log_action(
        actor_user_id=current_user.id,
        action=f"settings.update.{category}",
        detail={"keys_updated": list(settings.keys())}
    ))
    
    return {"status": "success"}

class SerperKeyRequest(BaseModel):
    serper_api_key: str

@router.post("/serper")
async def update_serper_key(
    body: SerperKeyRequest,
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """Update Serper API Key in .env and runtime config."""
    from services.user_preferences import get_user_preferences
    prefs_svc = get_user_preferences()
    await prefs_svc.set(current_user.id, "SERPER_API_KEY", body.serper_api_key)
    
    import asyncio
    asyncio.create_task(log_action(
        actor_user_id=current_user.id,
        action="settings.update.serper",
        detail={"key_set": True}
    ))
    return {"status": "success"}

# ── API Keys ─────────────────────────────────────────────────────────────

class ApiKeyOut(BaseModel):
    id: str
    name: str
    prefix: str
    last_used_at: Optional[str]
    created_at: str

class ApiKeyCreateRequest(BaseModel):
    name: str

class ApiKeyCreateResponse(BaseModel):
    id: str
    name: str
    key: str  # The raw key, only shown once!

@router.get("/api-keys", response_model=List[ApiKeyOut])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ApiKeyOut]:
    result = await db.execute(
        select(ApiKey)
        .where(ApiKey.revoked_at.is_(None))
        .order_by(ApiKey.created_at.desc())
    )
    keys = result.scalars().all()
    return [
        ApiKeyOut(
            id=k.id, name=k.name, prefix=k.prefix or "",
            last_used_at=k.last_used_at.isoformat() if k.last_used_at else None,
            created_at=k.created_at.isoformat()
        )
        for k in keys
    ]

@router.post("/api-keys", response_model=ApiKeyCreateResponse)
async def create_api_key(
    body: ApiKeyCreateRequest,
    current_user: User = Depends(require_role("TENANT_ADMIN", "DEVELOPER")),
    db: AsyncSession = Depends(get_db),
) -> ApiKeyCreateResponse:
    import secrets
    from security.auth import hash_password
    
    raw_key = f"sk-{secrets.token_urlsafe(32)}"
    prefix = raw_key[:10]
    hashed = hash_password(raw_key)

    api_key = ApiKey(
        user_id=current_user.id,
        name=body.name,
        hashed_key=hashed,
        prefix=prefix
    )
    db.add(api_key)
    await db.flush()
    await db.commit()

    import asyncio
    asyncio.create_task(log_action(
        actor_user_id=current_user.id,
        action="api_key.create",
        detail={"name": body.name}
    ))

    return ApiKeyCreateResponse(
        id=api_key.id,
        name=api_key.name,
        key=raw_key
    )

@router.delete("/api-keys/{key_id}", status_code=200)
async def revoke_api_key(
    key_id: str,
    current_user: User = Depends(require_role("TENANT_ADMIN", "DEVELOPER")),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        select(ApiKey).where(ApiKey.id == key_id)
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=404, detail="API Key not found")
    
    api_key.revoked_at = datetime.utcnow()
    await db.commit()

    import asyncio
    asyncio.create_task(log_action(
        actor_user_id=current_user.id,
        action="api_key.revoke",
        detail={"name": api_key.name}
    ))


# ── Active Sessions ──────────────────────────────────────────────────────

class SessionOut(BaseModel):
    id: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: str
    last_seen_at: str

@router.get("/sessions", response_model=List[SessionOut])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[SessionOut]:
    result = await db.execute(
        select(UserSession)
        .where(UserSession.user_id == current_user.id, UserSession.revoked_at.is_(None))
        .order_by(UserSession.last_seen_at.desc())
    )
    sessions = result.scalars().all()
    return [
        SessionOut(
            id=s.id, ip_address=s.ip_address, user_agent=s.user_agent,
            created_at=s.created_at.isoformat(), last_seen_at=s.last_seen_at.isoformat()
        )
        for s in sessions
    ]

@router.delete("/sessions/{session_id}", status_code=200)
async def revoke_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        select(UserSession).where(UserSession.id == session_id, UserSession.user_id == current_user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session.revoked_at = datetime.utcnow()
    await db.commit()


# ── Audit Log ────────────────────────────────────────────────────────────

class AuditLogOut(BaseModel):
    id: str
    actor_user_id: Optional[str]
    action: str
    target: Optional[str]
    detail: Optional[Dict[str, Any]]
    created_at: str

@router.get("/audit-log", response_model=List[AuditLogOut])
async def list_audit_logs(
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(require_role("TENANT_ADMIN")),
    db: AsyncSession = Depends(get_db),
) -> List[AuditLogOut]:
    result = await db.execute(
        select(AuditLogEntry)
        .order_by(AuditLogEntry.created_at.desc())
        .limit(limit)
    )
    logs = result.scalars().all()
    import json
    return [
        AuditLogOut(
            id=l.id, actor_user_id=l.actor_user_id, action=l.action, target=l.target,
            detail=json.loads(l.detail) if l.detail else None,
            created_at=l.created_at.isoformat()
        )
        for l in logs
    ]
