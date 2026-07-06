"""
connectors/google_drive/auth.py

Google OAuth2 authentication for Drive connector.

Uses Drive-specific scopes (readonly) separate from the existing
user login OAuth flow (openid email profile).

Scopes:
  - https://www.googleapis.com/auth/drive.readonly
    → read-only access to all files in user's Drive
  - https://www.googleapis.com/auth/drive.metadata.readonly
    → read file metadata without downloading content
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from urllib.parse import urlencode

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

GOOGLE_AUTH_BASE = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"

DRIVE_SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/drive.metadata.readonly",
    "openid",
    "email",
]


def build_auth_url(state: str, redirect_uri: str) -> str:
    """
    Build the Google OAuth2 authorization URL with Drive scopes.

    Parameters
    ----------
    state : str
        Random CSRF token to include in the URL (stored in session).
    redirect_uri : str
        Where Google should redirect after authorization.
    """
    cfg = get_settings()
    params = {
        "client_id": cfg.connectors.google_drive_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(DRIVE_SCOPES),
        "access_type": "offline",   # Required to get a refresh_token
        "prompt": "consent",         # Always show consent to ensure refresh_token is issued
        "state": state,
    }
    return f"{GOOGLE_AUTH_BASE}?{urlencode(params)}"


async def exchange_code(auth_code: str, redirect_uri: str) -> dict:
    """
    Exchange an authorization code for access and refresh tokens.

    Returns
    -------
    dict with keys:
        access_token, refresh_token, expires_in, token_type, scope
    """
    cfg = get_settings()
    payload = {
        "code": auth_code,
        "client_id": cfg.connectors.google_drive_client_id,
        "client_secret": cfg.connectors.google_drive_client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(GOOGLE_TOKEN_URL, data=payload)
        resp.raise_for_status()
        data = resp.json()

    if "error" in data:
        raise ValueError(f"Google token exchange failed: {data['error']} — {data.get('error_description', '')}")

    if "refresh_token" not in data:
        raise ValueError(
            "Google did not return a refresh_token. "
            "Make sure 'access_type=offline' and 'prompt=consent' are set."
        )

    # Compute absolute expiry time
    expires_in = data.get("expires_in", 3600)
    data["expires_at"] = (
        datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    ).isoformat()

    logger.info("Google Drive OAuth token exchange succeeded.")
    return data


async def refresh_access_token(refresh_token: str) -> dict:
    """
    Use a refresh token to get a new access token.

    Returns updated token dict (no new refresh_token is issued).
    """
    cfg = get_settings()
    payload = {
        "refresh_token": refresh_token,
        "client_id": cfg.connectors.google_drive_client_id,
        "client_secret": cfg.connectors.google_drive_client_secret,
        "grant_type": "refresh_token",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(GOOGLE_TOKEN_URL, data=payload)
        resp.raise_for_status()
        data = resp.json()

    if "error" in data:
        raise ValueError(f"Google token refresh failed: {data['error']}")

    expires_in = data.get("expires_in", 3600)
    data["expires_at"] = (
        datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    ).isoformat()

    logger.debug("Google Drive access token refreshed.")
    return data


async def revoke_token(token: str) -> None:
    """Revoke an access or refresh token."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(GOOGLE_REVOKE_URL, params={"token": token})
        if resp.status_code not in (200, 400):  # 400 = already revoked, ok
            logger.warning("Token revocation returned %s", resp.status_code)


def is_token_expired(expires_at_iso: Optional[str], buffer_seconds: int = 300) -> bool:
    """Check if the access token is expired (or expires within buffer_seconds)."""
    if not expires_at_iso:
        return True
    try:
        expires_at = datetime.fromisoformat(expires_at_iso)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) >= (expires_at - timedelta(seconds=buffer_seconds))
    except Exception:
        return True


__all__ = [
    "build_auth_url",
    "exchange_code",
    "refresh_access_token",
    "revoke_token",
    "is_token_expired",
    "DRIVE_SCOPES",
]
