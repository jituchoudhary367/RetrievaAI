"""
security/auth.py

JWT token creation, validation, and FastAPI dependencies for auth + RBAC.

Key patterns:
  - `get_current_user()`  — validates Bearer token, checks jti against
    UserSession table, returns the User row. Used as a FastAPI dependency.
  - `require_role(*roles)` — dependency factory that wraps get_current_user
    and adds a role check; use with `Depends(require_role("TENANT_ADMIN"))`.
  - `create_access_token()` / `create_refresh_token()` — issue JWTs with
    `jti` (session-level) and `token_version` (kill-all) claims.

JTI vs token_version (§1.8):
  - `token_version` on the User row: incremented by password reset — kills
    every session at once.
  - `jti` on UserSession: checked individually — lets one device be revoked
    without affecting others.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from db.engine import get_db
from db.models.user import User, UserSession

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# Password hashing
# -------------------------------------------------------------------------

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


# -------------------------------------------------------------------------
# Token creation
# -------------------------------------------------------------------------

def _settings():
    return get_settings().security


def create_access_token(
    user_id: str,
    tenant_id: str,
    roles: List[str],
    token_version: int,
    jti: Optional[str] = None,
) -> str:
    cfg = _settings()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=cfg.jwt_access_token_expire_minutes)
    payload = {
        "sub": user_id,
        "tid": tenant_id,
        "roles": roles,
        "tv": token_version,          # token_version — for kill-all
        "jti": jti or str(uuid.uuid4()),  # jti — for per-session revoke
        "iat": now,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, cfg.jwt_secret_key, algorithm=cfg.jwt_algorithm)


def create_refresh_token(user_id: str, jti: str) -> str:
    cfg = _settings()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=cfg.jwt_refresh_token_expire_days)
    payload = {
        "sub": user_id,
        "jti": jti,
        "iat": now,
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, cfg.jwt_secret_key, algorithm=cfg.jwt_algorithm)


# -------------------------------------------------------------------------
# Token validation
# -------------------------------------------------------------------------

_bearer_scheme = HTTPBearer(auto_error=False)


def _decode_token(token: str) -> dict:
    cfg = _settings()
    try:
        return jwt.decode(token, cfg.jwt_secret_key, algorithms=[cfg.jwt_algorithm])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency — validates Bearer JWT and returns the User row.

    Checks:
      1. Token is well-formed and not expired.
      2. `token_version` in token matches User.token_version (kill-all guard).
      3. `jti` in token has a non-revoked UserSession row (per-device guard).
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = _decode_token(credentials.credentials)

    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    user_id: str = payload.get("sub", "")
    jti: str = payload.get("jti", "")
    token_version: int = payload.get("tv", -1)

    # Fetch user
    result = await db.execute(select(User).where(User.id == user_id))
    user: Optional[User] = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    # Check kill-all version
    if user.token_version != token_version:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session invalidated")

    # Check per-session revocation
    sess_result = await db.execute(
        select(UserSession).where(
            UserSession.session_jti == jti,
            UserSession.revoked_at.is_(None),
        )
    )
    session = sess_result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session revoked or not found")

    # Update last_seen
    session.last_seen_at = datetime.now(timezone.utc)

    return user


def require_role(*roles: str):
    """
    Dependency factory — returns a dependency that enforces role membership.

    Usage:
        @router.delete(...)
        async def delete_doc(user: User = Depends(require_role("TENANT_ADMIN"))):
            ...
    """
    async def _check(user: User = Depends(get_current_user)) -> User:
        user_roles = set(user.roles.split(",")) if user.roles else set()
        if not user_roles.intersection(roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {list(roles)}",
            )
        return user
    return _check


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> Optional[str]:
    """
    Returns the user_id from the token without hitting the DB.
    Used for telemetry where we don't want to fail the request on auth errors.
    """
    if credentials is None:
        return None
    try:
        payload = _decode_token(credentials.credentials)
        return payload.get("sub")
    except Exception:
        return None
