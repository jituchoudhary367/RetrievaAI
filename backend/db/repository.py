"""
db/repository.py

Minimal async CRUD methods for auth and tenancy integration.
"""

from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.user import User
from db.models.invite import Invite
from db.models.auth_token import AuthToken

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
        
    async def create(self, email: str, hashed_password: str, roles: list[str]) -> User:
        user = User(
            email=email,
            hashed_password=hashed_password,
            roles=",".join(roles)
        )
        self.session.add(user)
        await self.session.flush()
        return user


class InviteRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def get_by_token(self, token: str) -> Optional[Invite]:
        result = await self.session.execute(select(Invite).where(Invite.token == token))
        return result.scalar_one_or_none()
        
    async def create(self, email: str, token: str, role: str, expires_at) -> Invite:
        invite = Invite(
            email=email,
            token=token,
            role=role,
            expires_at=expires_at
        )
        self.session.add(invite)
        await self.session.flush()
        return invite
        
    async def mark_accepted(self, invite_id: str, accepted_at) -> None:
        await self.session.execute(
            update(Invite).where(Invite.id == invite_id).values(accepted_at=accepted_at)
        )
        await self.session.flush()

class AuthTokenRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: str, purpose: str, token: str, expires_at) -> AuthToken:
        auth_token = AuthToken(
            user_id=user_id,
            purpose=purpose,
            token=token,
            expires_at=expires_at
        )
        self.session.add(auth_token)
        await self.session.flush()
        return auth_token

    async def get_valid(self, token: str, purpose: str, now) -> Optional[AuthToken]:
        # checks both expires_at and used_at is null together
        result = await self.session.execute(
            select(AuthToken).where(
                AuthToken.token == token,
                AuthToken.purpose == purpose,
                AuthToken.used_at.is_(None),
                AuthToken.expires_at > now
            )
        )
        return result.scalar_one_or_none()

    async def mark_used(self, token: str, used_at) -> None:
        await self.session.execute(
            update(AuthToken).where(AuthToken.token == token).values(used_at=used_at)
        )
        await self.session.flush()

