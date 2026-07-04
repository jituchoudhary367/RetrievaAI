"""
routes/auth.py

Authentication and user management endpoints.
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    SignupRequest, LoginRequest, InviteRequest, AcceptInviteRequest,
    AuthResponse, InviteResponse, SignupResponse, MessageResponse,
    VerifyEmailRequest, ResendVerificationRequest, RequestPasswordResetRequest, ResetPasswordRequest
)
from db.engine import get_db
from security.auth import get_current_user
from db.models.user import User
from services.auth_service import (
    signup, login, invite_user, accept_invite, verify_email,
    resend_verification_email, request_password_reset, reset_password
)

router = APIRouter(tags=["Auth"])

@router.post("/signup", response_model=SignupResponse)
async def signup_route(
    request: SignupRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await signup(
        session=db,
        email=request.email,
        password=request.password
    )
    return SignupResponse(
        userId=result.user_id,
        email=result.email
    )


@router.post("/login", response_model=AuthResponse)
async def login_route(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    tokens = await login(
        session=db,
        email=request.email,
        password=request.password
    )
    return AuthResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
        user_id=tokens.user_id,
        roles=tokens.roles
    )


@router.post("/invite", response_model=InviteResponse)
async def invite_route(
    request: InviteRequest,
    req: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    invite = await invite_user(
        session=db,
        email=request.email,
        role=request.role
    )
    
    # Construct an invite link using the request's base URL.
    # We fallback to a hardcoded frontend URL if it's not possible to deduce safely, 
    # but request.base_url works well enough for this.
    base_url = str(req.base_url).rstrip("/")
    invite_link = f"{base_url}/accept-invite?token={invite.token}"
    
    return InviteResponse(
        invite_link=invite_link,
        expires_at=invite.expires_at
    )


@router.post("/accept-invite", response_model=AuthResponse)
async def accept_invite_route(
    request: AcceptInviteRequest,
    db: AsyncSession = Depends(get_db)
):
    tokens = await accept_invite(
        session=db,
        token=request.token,
        password=request.password
    )
    return AuthResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
        user_id=tokens.user_id,
        roles=tokens.roles
    )


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email_route(
    request: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db)
):
    await verify_email(db, request.token)
    return MessageResponse(message="Email verified successfully")


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification_route(
    request: ResendVerificationRequest,
    db: AsyncSession = Depends(get_db)
):
    await resend_verification_email(db, request.email)
    return MessageResponse(message="If an account exists, a verification email has been sent.")


@router.post("/request-password-reset", response_model=MessageResponse)
async def request_password_reset_route(
    request: RequestPasswordResetRequest,
    db: AsyncSession = Depends(get_db)
):
    await request_password_reset(db, request.email)
    return MessageResponse(message="If an account exists, a password reset email has been sent.")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password_route(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    await reset_password(db, request.token, request.newPassword)
    return MessageResponse(message="Password reset successfully")
