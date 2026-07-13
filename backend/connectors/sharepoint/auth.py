import os
from typing import Dict, Any, Tuple
import httpx
from datetime import datetime, timezone, timedelta

from connectors.base.exceptions import ConnectorAuthError

MICROSOFT_CLIENT_ID = os.environ.get("SHAREPOINT_CLIENT_ID", os.environ.get("MICROSOFT_CLIENT_ID", "mock-sp-client-id"))
MICROSOFT_CLIENT_SECRET = os.environ.get("SHAREPOINT_CLIENT_SECRET", os.environ.get("MICROSOFT_CLIENT_SECRET", "mock-sp-client-secret"))
MICROSOFT_REDIRECT_URI = os.environ.get("SHAREPOINT_REDIRECT_URI", os.environ.get("MICROSOFT_REDIRECT_URI", "http://localhost:8000/api/connectors/oauth/callback"))

AUTH_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
SCOPES = "offline_access Sites.Read.All Files.Read.All User.Read"

def get_auth_url(state: str) -> str:
    """Generate the Microsoft OAuth2 authorization URL."""
    return (
        f"{AUTH_URL}?client_id={MICROSOFT_CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={MICROSOFT_REDIRECT_URI}"
        f"&scope={SCOPES.replace(' ', '%20')}"
        f"&state={state}"
        f"&response_mode=query"
    )

async def exchange_code(code: str) -> Tuple[Dict[str, Any], datetime]:
    """Exchange auth code for tokens."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            TOKEN_URL,
            data={
                "client_id": MICROSOFT_CLIENT_ID,
                "client_secret": MICROSOFT_CLIENT_SECRET,
                "code": code,
                "redirect_uri": MICROSOFT_REDIRECT_URI,
                "grant_type": "authorization_code",
            }
        )
        if not response.is_success:
            raise ConnectorAuthError(f"Failed to exchange code: {response.text}")
        
        data = response.json()
        expires_in = data.get("expires_in", 3600)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        return data, expires_at

async def refresh_token(refresh_token_str: str) -> Tuple[Dict[str, Any], datetime]:
    """Refresh an existing token."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            TOKEN_URL,
            data={
                "client_id": MICROSOFT_CLIENT_ID,
                "client_secret": MICROSOFT_CLIENT_SECRET,
                "refresh_token": refresh_token_str,
                "grant_type": "refresh_token",
            }
        )
        if not response.is_success:
            raise ConnectorAuthError(f"Failed to refresh token: {response.text}")
            
        data = response.json()
        expires_in = data.get("expires_in", 3600)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        return data, expires_at
