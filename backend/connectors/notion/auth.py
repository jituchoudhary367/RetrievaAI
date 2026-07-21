import os
from typing import Dict, Any, Tuple
import httpx
from datetime import datetime, timezone, timedelta
import base64

from connectors.base.exceptions import ConnectorAuthError

NOTION_CLIENT_ID = os.environ.get("NOTION_CLIENT_ID", "mock-notion-client-id")
NOTION_CLIENT_SECRET = os.environ.get("NOTION_CLIENT_SECRET", "mock-notion-client-secret")
NOTION_REDIRECT_URI = os.environ.get("NOTION_REDIRECT_URI", "http://localhost:8000/api/connectors/oauth/callback")

AUTH_URL = "https://api.notion.com/v1/oauth/authorize"
TOKEN_URL = "https://api.notion.com/v1/oauth/token"


def get_auth_url(state: str) -> str:
    """Generate the Notion OAuth2 authorization URL."""
    return (
        f"{AUTH_URL}?client_id={NOTION_CLIENT_ID}"
        f"&response_type=code"
        f"&owner=user"
        f"&redirect_uri={NOTION_REDIRECT_URI}"
        f"&state={state}"
    )


async def exchange_code(code: str) -> Tuple[Dict[str, Any], datetime]:
    """Exchange auth code for tokens using HTTP Basic Auth (Notion requires this)."""
    credentials = base64.b64encode(
        f"{NOTION_CLIENT_ID}:{NOTION_CLIENT_SECRET}".encode()
    ).decode("utf-8")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            TOKEN_URL,
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/json",
            },
            json={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": NOTION_REDIRECT_URI,
            },
        )
        if not response.is_success:
            raise ConnectorAuthError(f"Failed to exchange code: {response.text}")

        data = response.json()
        # Notion tokens don't expire (access_token is permanent unless revoked),
        # but we keep this pattern consistent with other adapters.
        expires_at = datetime.now(timezone.utc) + timedelta(days=365)
        return data, expires_at


async def refresh_token(refresh_token_str: str) -> Tuple[Dict[str, Any], datetime]:
    """Notion does not support refresh tokens — access tokens are permanent."""
    # Return a sentinel so callers still work without crashing.
    return {"access_token": refresh_token_str}, datetime.now(timezone.utc) + timedelta(days=365)
