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

class AuthError(HTTPException):
    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )

# -------------------------------------------------------------------------
# Token creation
# -------------------------------------------------------------------------

def _settings():
    return get_settings().security


def create_access_token(
    user_id: str,
    roles: List[str],
    token_version: int,
    jti: Optional[str] = None,
    avatar_url: Optional[str] = None,
    name: Optional[str] = None,
    email: Optional[str] = None,
) -> str:
    cfg = _settings()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=cfg.jwt_access_token_expire_minutes)
    payload = {
        "sub": user_id,
        "roles": roles,
        "tv": token_version,          # token_version — for kill-all
        "jti": jti or str(uuid.uuid4()),  # jti — for per-session revoke
        "avatar_url": avatar_url,
        "name": name,
        "email": email,
        "iat": now,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, cfg.jwt_secret_key, algorithm=cfg.jwt_algorithm)


def create_refresh_token(user_id: str, jti: str, token_version: int) -> str:
    cfg = _settings()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=cfg.jwt_refresh_token_expire_days)
    payload = {
        "sub": user_id,
        "jti": jti,
        "tv": token_version,
        "iat": now,
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, cfg.jwt_secret_key, algorithm=cfg.jwt_algorithm)

def verify_refresh_token(token: str, current_token_version: int) -> dict:
    payload = _decode_token(token)
    if payload.get("type") != "refresh":
        raise AuthError("Invalid token type")
    
    token_version = payload.get("tv")
    if token_version is None or token_version != current_token_version:
        raise AuthError("Session invalidated")
        
    return payload


# -------------------------------------------------------------------------
# Token validation
# -------------------------------------------------------------------------

_bearer_scheme = HTTPBearer(auto_error=False)


def _decode_token(token: str) -> dict:
    cfg = _settings()
    try:
        return jwt.decode(token, cfg.jwt_secret_key, algorithms=[cfg.jwt_algorithm])
    except JWTError as exc:
        raise AuthError("Invalid or expired token") from exc

def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> str:
    """
    FastAPI dependency — validates Bearer JWT and returns the User ID.
    Does not query the database.
    """
    if credentials is None:
        raise AuthError("Not authenticated")

    try:
        payload = _decode_token(credentials.credentials)
    except Exception as e:
        logger.warning(f"Token decode failed: {e}")
        raise AuthError("Invalid token")

    if payload.get("type") != "access":
        raise AuthError("Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthError("Invalid token payload")
        
    return user_id


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
        logger.warning("No credentials provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = _decode_token(credentials.credentials)
    except Exception as e:
        logger.warning(f"Token decode failed: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if payload.get("type") != "access":
        logger.warning(f"Invalid token type: {payload.get('type')}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    user_id: str = payload.get("sub", "")
    jti: str = payload.get("jti", "")
    token_version: int = payload.get("tv", -1)

    # Fetch user
    result = await db.execute(select(User).where(User.id == user_id))
    user: Optional[User] = result.scalar_one_or_none()
    if user is None or not user.is_active:
        logger.warning(f"User not found or inactive: {user_id}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    # Check kill-all version
    if user.token_version != token_version:
        logger.warning(f"Token version mismatch. DB: {user.token_version}, Token: {token_version}")
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
        logger.warning(f"Session not found or revoked for JTI: {jti}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session revoked or not found")

    # Update last_seen — fire-and-forget; don't let DB timeout crash the request
    try:
        now = datetime.now(timezone.utc)
        if not session.last_seen_at or (now - session.last_seen_at.replace(tzinfo=timezone.utc)).total_seconds() > 60:
            session.last_seen_at = now
    except Exception as _lsa_exc:
        logger.debug("last_seen_at update skipped: %s", _lsa_exc)

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
