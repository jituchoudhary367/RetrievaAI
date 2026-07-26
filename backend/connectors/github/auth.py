import os
from typing import Dict, Any, Tuple
import httpx
from datetime import datetime, timezone, timedelta

from connectors.base.exceptions import ConnectorAuthError

GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID", "mock-github-client-id")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "mock-github-client-secret")
GITHUB_REDIRECT_URI = os.environ.get("GITHUB_REDIRECT_URI", "http://localhost:8000/api/connectors/oauth/callback")

AUTH_URL = "https://github.com/login/oauth/authorize"
TOKEN_URL = "https://github.com/login/oauth/access_token"
API_URL = "https://api.github.com"

# We request scopes necessary for reading user repos (including private if authorized)
SCOPES = "repo,read:user,user:email"

def get_auth_url(state: str) -> str:
    """Generate the GitHub OAuth2 authorization URL."""
    return (
        f"{AUTH_URL}?client_id={GITHUB_CLIENT_ID}"
        f"&scope={SCOPES}"
        f"&redirect_uri={GITHUB_REDIRECT_URI}"
        f"&state={state}"
    )

async def exchange_code(code: str) -> Tuple[Dict[str, Any], datetime]:
    """Exchange auth code for tokens."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": GITHUB_REDIRECT_URI,
            }
        )
        if not response.is_success:
            raise ConnectorAuthError(f"Failed to exchange code: {response.text}")

        data = response.json()
        if "error" in data:
            raise ConnectorAuthError(f"GitHub OAuth error: {data.get('error_description')}")

        access_token = data.get("access_token")
        
        # Get user details
        user_resp = await client.get(
            f"{API_URL}/user",
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github.v3+json"}
        )
        user_resp.raise_for_status()
        user_data = user_resp.json()

        token_data = {
            "access_token": access_token,
            "provider_user_id": str(user_data.get("id")),
            "provider_username": user_data.get("login"),
            "provider_email": user_data.get("email"),
        }
        
        # GitHub OAuth App tokens without expiration enabled are permanent
        # If refresh tokens are enabled, 'refresh_token' and 'expires_in' would be present.
        expires_in = data.get("expires_in")
        if expires_in:
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))
            token_data["refresh_token"] = data.get("refresh_token")
        else:
            expires_at = datetime.now(timezone.utc) + timedelta(days=365)
            
        return token_data, expires_at

async def refresh_token(refresh_token_str: str) -> Tuple[Dict[str, Any], datetime]:
    """Refresh an existing token (if token expiration is enabled on the OAuth app)."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "refresh_token": refresh_token_str,
                "grant_type": "refresh_token",
            }
        )
        if not response.is_success:
            raise ConnectorAuthError(f"Failed to refresh token: {response.text}")

        data = response.json()
        if "error" in data:
            raise ConnectorAuthError(f"GitHub OAuth error: {data.get('error_description')}")

        token_data = {
            "access_token": data.get("access_token"),
            "refresh_token": data.get("refresh_token"),
        }
        expires_in = data.get("expires_in")
        if expires_in:
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))
        else:
            expires_at = datetime.now(timezone.utc) + timedelta(days=365)
            
        return token_data, expires_at
