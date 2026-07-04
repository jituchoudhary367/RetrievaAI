"""
services/auth_service.py

Handles login, signup, and invites, delegating to the Repositories and Token generators.
"""

import logging
import secrets
import re
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from db.repository import UserRepository, InviteRepository, AuthTokenRepository
from security.passwords import hash_password, verify_password
from security.auth import create_access_token, create_refresh_token, AuthError
from services.email_service import EmailService
from db.models.user import UserSession
import redis

logger = logging.getLogger(__name__)

class AuthServiceError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
        )

class EmailNotVerifiedError(AuthServiceError):
    pass

@dataclass
class SignupResult:
    user_id: str
    email: str


@dataclass
class AuthTokens:
    access_token: str
    refresh_token: str
    expires_in: int
    user_id: str
    roles: List[str]


@dataclass
class InviteRecord:
    token: str
    expires_at: datetime





async def check_email_rate_limit(email: str) -> None:
    cfg = get_settings().redis
    try:
        # Simple redis ratelimit logic using redis-py
        r = redis.Redis(host=cfg.host, port=cfg.port, db=cfg.db, password=cfg.password, ssl=cfg.ssl)
        key = f"rate_limit:email:{email}"
        # limit to 1 per 5 minutes (300 seconds)
        count = r.incr(key)
        if count == 1:
            r.expire(key, 300)
        else:
            raise AuthServiceError("Rate limit exceeded")
    except redis.RedisError as e:
        logger.error(f"Redis error during rate limiting: {e}")
        pass # allow if redis is down? The prompt says "Raises the same generic AuthServiceError as a normal failure on the outside". Actually if rate limited, raise AuthServiceError.
        
async def signup(session: AsyncSession, email: str, password: str) -> SignupResult:
    user_repo = UserRepository(session)
    token_repo = AuthTokenRepository(session)
    
    existing_user = await user_repo.get_by_email(email)
    if existing_user:
        raise AuthServiceError("Invalid email or password")
        
    # create user (is_verified defaults to False)
    hashed = hash_password(password)
    roles = ["admin"]
    user = await user_repo.create(email=email, hashed_password=hashed, roles=roles)
    
    # create verification token
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=1)
    await token_repo.create(user.id, "email_verify", token, expires_at)
    
    # send email
    email_service = EmailService()
    email_service.send_verification_email(email, token)
    
    return SignupResult(
        user_id=user.id,
        email=email
    )


async def login(session: AsyncSession, email: str, password: str) -> AuthTokens:
    user_repo = UserRepository(session)
    user = await user_repo.get_by_email(email)
    
    # Generic error message
    generic_error = "Invalid email or password"
    if not user or not user.is_active:
        raise AuthServiceError(generic_error)
        
    if not verify_password(password, user.hashed_password):
        raise AuthServiceError(generic_error)
        
    if not user.is_verified:
        raise EmailNotVerifiedError("Email not verified")
        
    roles = user.roles.split(",") if user.roles else []
    
    cfg = get_settings().security
    jti = secrets.token_hex(16)
    
    access_token = create_access_token(
        user_id=user.id,
        roles=roles,
        token_version=user.token_version,
        jti=jti,
        email=user.email
    )
    refresh_token = create_refresh_token(
        user_id=user.id,
        jti=jti,
        token_version=user.token_version
    )
    
    # Create the UserSession record
    now = datetime.now(timezone.utc)
    new_session = UserSession(
        user_id=user.id,
        session_jti=jti,
        created_at=now,
        last_seen_at=now,
    )
    session.add(new_session)
    await session.commit()
    
    return AuthTokens(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=cfg.jwt_access_token_expire_minutes * 60,
        user_id=user.id,
        roles=roles
    )


async def invite_user(session: AsyncSession, email: str, role: str) -> InviteRecord:
    invite_repo = InviteRepository(session)
    
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    invite = await invite_repo.create(
        email=email,
        token=token,
        role=role,
        expires_at=expires_at
    )
    
    return InviteRecord(
        token=invite.token,
        expires_at=invite.expires_at
    )


async def accept_invite(session: AsyncSession, token: str, password: str) -> AuthTokens:
    invite_repo = InviteRepository(session)
    user_repo = UserRepository(session)
    
    invite = await invite_repo.get_by_token(token)
    
    generic_error = "Invalid or expired invite"
    
    if not invite:
        raise AuthServiceError(generic_error)
        
    if invite.accepted_at:
        raise AuthServiceError(generic_error)
        
    if invite.expires_at < datetime.now(timezone.utc):
        raise AuthServiceError(generic_error)
        
    hashed = hash_password(password)
    roles = [invite.role]
    
    # create user (auto-verified)
    user = await user_repo.create(
        email=invite.email,
        hashed_password=hashed,
        roles=roles
    )
    user.is_verified = True
    
    await invite_repo.mark_accepted(invite.id, datetime.now(timezone.utc))
    
    cfg = get_settings().security
    jti = secrets.token_hex(16)
    
    access_token = create_access_token(
        user_id=user.id,
        roles=roles,
        token_version=user.token_version,
        jti=jti,
        email=user.email
    )
    refresh_token = create_refresh_token(
        user_id=user.id,
        jti=jti,
        token_version=user.token_version
    )
    
    # Create the UserSession record
    now = datetime.now(timezone.utc)
    new_session = UserSession(
        user_id=user.id,
        session_jti=jti,
        created_at=now,
        last_seen_at=now,
    )
    session.add(new_session)
    await session.commit()
    
    return AuthTokens(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=cfg.jwt_access_token_expire_minutes * 60,
        user_id=user.id,
        roles=roles
    )


async def verify_email(session: AsyncSession, token: str) -> None:
    token_repo = AuthTokenRepository(session)
    user_repo = UserRepository(session)
    
    auth_token = await token_repo.get_valid(token, "email_verify", datetime.now(timezone.utc))
    if not auth_token:
        raise AuthServiceError("Invalid or expired token")
        
    from db.models.user import User
    from sqlalchemy import select
    result = await session.execute(select(User).where(User.id == auth_token.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise AuthServiceError("Invalid or expired token")
        
    user.is_verified = True
    await token_repo.mark_used(token, datetime.now(timezone.utc))


async def resend_verification_email(session: AsyncSession, email: str) -> None:
    await check_email_rate_limit(email)
    
    user_repo = UserRepository(session)
    token_repo = AuthTokenRepository(session)
    
    user = await user_repo.get_by_email(email)
    if user and not user.is_verified:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(days=1)
        await token_repo.create(user.id, "email_verify", token, expires_at)
        
        email_service = EmailService()
        email_service.send_verification_email(email, token)


async def request_password_reset(session: AsyncSession, email: str) -> None:
    await check_email_rate_limit(email)
    
    user_repo = UserRepository(session)
    token_repo = AuthTokenRepository(session)
    
    user = await user_repo.get_by_email(email)
    if user:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        await token_repo.create(user.id, "password_reset", token, expires_at)
        
        email_service = EmailService()
        email_service.send_password_reset_email(email, token)


async def reset_password(session: AsyncSession, token: str, new_password: str) -> None:
    token_repo = AuthTokenRepository(session)
    
    auth_token = await token_repo.get_valid(token, "password_reset", datetime.now(timezone.utc))
    if not auth_token:
        raise AuthServiceError("Invalid or expired token")
        
    from db.models.user import User
    from sqlalchemy import select
    result = await session.execute(select(User).where(User.id == auth_token.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise AuthServiceError("Invalid or expired token")
        
    user.hashed_password = hash_password(new_password)
    user.token_version += 1
    await token_repo.mark_used(token, datetime.now(timezone.utc))

async def login_or_create_oauth_user(session: AsyncSession, email: str, display_name: str, provider: str, avatar_url: str = None) -> AuthTokens:
    user_repo = UserRepository(session)
    user = await user_repo.get_by_email(email)
    
    if user and avatar_url and user.avatar_url != avatar_url:
        user.avatar_url = avatar_url
        session.add(user)
        
    if not user:
        # Create a new user with a random un-guessable password
        # random password since they use OAuth
        hashed = hash_password(secrets.token_urlsafe(32))
        
        user = await user_repo.create(
            email=email, 
            hashed_password=hashed, 
            roles=["admin"]
        )
        user.display_name = display_name
        user.avatar_url = avatar_url
        user.is_verified = True # OAuth implies verified
        session.add(user)
        await session.flush()
    
    if not user.is_active:
        raise AuthServiceError("Account is inactive")
        
    cfg = get_settings().security
    jti = secrets.token_hex(16)
    roles = user.roles.split(",") if user.roles else []
    
    access_token = create_access_token(
        user_id=user.id,
        roles=roles,
        token_version=user.token_version,
        jti=jti,
        avatar_url=user.avatar_url,
        name=user.display_name,
        email=user.email
    )
    refresh_token = create_refresh_token(
        user_id=user.id,
        jti=jti,
        token_version=user.token_version
    )
    
    # Create the UserSession record
    now = datetime.now(timezone.utc)
    new_session = UserSession(
        user_id=user.id,
        session_jti=jti,
        created_at=now,
        last_seen_at=now,
    )
    session.add(new_session)
    await session.commit()
    
    return AuthTokens(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=cfg.jwt_access_token_expire_minutes * 60,
        user_id=user.id,
        roles=roles
    )
