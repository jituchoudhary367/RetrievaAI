import os
from typing import Dict, Any, Tuple
import httpx
from datetime import datetime, timezone, timedelta

from connectors.base.exceptions import ConnectorAuthError

ATLASSIAN_CLIENT_ID = os.environ.get("CONFLUENCE_CLIENT_ID", "mock-confluence-client-id")
ATLASSIAN_CLIENT_SECRET = os.environ.get("CONFLUENCE_CLIENT_SECRET", "mock-confluence-client-secret")
ATLASSIAN_REDIRECT_URI = os.environ.get("CONFLUENCE_REDIRECT_URI", "http://localhost:8000/api/connectors/oauth/callback")

AUTH_URL = "https://auth.atlassian.com/authorize"
TOKEN_URL = "https://auth.atlassian.com/oauth/token"
SCOPES = "read:confluence-space.summary read:confluence-props read:confluence-content.all read:confluence-content.summary offline_access"

def get_auth_url(state: str) -> str:
    """Generate the Atlassian OAuth2 authorization URL."""
    return (
        f"{AUTH_URL}?audience=api.atlassian.com"
        f"&client_id={ATLASSIAN_CLIENT_ID}"
        f"&scope={SCOPES.replace(' ', '%20')}"
        f"&redirect_uri={ATLASSIAN_REDIRECT_URI}"
        f"&state={state}"
        f"&response_type=code"
        f"&prompt=consent"
    )

async def exchange_code(code: str) -> Tuple[Dict[str, Any], datetime]:
    """Exchange auth code for tokens."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            TOKEN_URL,
            json={
                "client_id": ATLASSIAN_CLIENT_ID,
                "client_secret": ATLASSIAN_CLIENT_SECRET,
                "code": code,
                "redirect_uri": ATLASSIAN_REDIRECT_URI,
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
            json={
                "client_id": ATLASSIAN_CLIENT_ID,
                "client_secret": ATLASSIAN_CLIENT_SECRET,
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
