import os
from typing import Dict, Any, Tuple
import httpx
from datetime import datetime, timezone, timedelta

from connectors.base.exceptions import ConnectorAuthError

DROPBOX_APP_KEY = os.environ.get("DROPBOX_APP_KEY", "mock-dropbox-app-key")
DROPBOX_APP_SECRET = os.environ.get("DROPBOX_APP_SECRET", "mock-dropbox-app-secret")
DROPBOX_REDIRECT_URI = os.environ.get(
    "DROPBOX_REDIRECT_URI",
    "http://localhost:8000/api/connectors/oauth/callback"
)

AUTH_URL = "https://www.dropbox.com/oauth2/authorize"
TOKEN_URL = "https://api.dropboxapi.com/oauth2/token"
REVOKE_URL = "https://api.dropboxapi.com/2/auth/token/revoke"


def get_auth_url(state: str) -> str:
    """Generate the Dropbox OAuth2 authorization URL with PKCE-like short-lived token."""
    return (
        f"{AUTH_URL}?client_id={DROPBOX_APP_KEY}"
        f"&response_type=code"
        f"&redirect_uri={DROPBOX_REDIRECT_URI}"
        f"&state={state}"
        f"&token_access_type=offline"  # Request refresh token
    )


async def exchange_code(code: str) -> Tuple[Dict[str, Any], datetime]:
    """Exchange auth code for access + refresh tokens."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            TOKEN_URL,
            data={
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": DROPBOX_REDIRECT_URI,
            },
            auth=(DROPBOX_APP_KEY, DROPBOX_APP_SECRET),
        )
        if not response.is_success:
            raise ConnectorAuthError(f"Failed to exchange code: {response.text}")

        data = response.json()
        if "error" in data:
            raise ConnectorAuthError(f"Dropbox OAuth error: {data.get('error_description', data['error'])}")

        token_data = {
            "access_token": data.get("access_token"),
            "refresh_token": data.get("refresh_token"),
            "provider_user_id": data.get("account_id"),
            "uid": data.get("uid"),
            "team_name": data.get("team_name"),
        }

        expires_in = data.get("expires_in", 14400)  # Dropbox tokens expire in 4hrs by default
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))
        return token_data, expires_at


async def refresh_token(refresh_token_str: str) -> Tuple[Dict[str, Any], datetime]:
    """Refresh a Dropbox access token using the stored refresh token."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token_str,
            },
            auth=(DROPBOX_APP_KEY, DROPBOX_APP_SECRET),
        )
        if not response.is_success:
            raise ConnectorAuthError(f"Failed to refresh token: {response.text}")

        data = response.json()
        if "error" in data:
            raise ConnectorAuthError(f"Dropbox refresh error: {data.get('error_description', data['error'])}")

        token_data = {
            "access_token": data.get("access_token"),
            "refresh_token": refresh_token_str,  # Dropbox keeps the same refresh token
        }
        expires_in = data.get("expires_in", 14400)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))
        return token_data, expires_at


async def revoke_token(access_token: str) -> None:
    """Revoke a Dropbox access token."""
    async with httpx.AsyncClient() as client:
        await client.post(
            REVOKE_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
