import os
from typing import Dict, Any, Tuple
import httpx
from datetime import datetime, timezone, timedelta

from connectors.base.exceptions import ConnectorAuthError

SLACK_CLIENT_ID = os.environ.get("SLACK_CLIENT_ID", "mock-slack-client-id")
SLACK_CLIENT_SECRET = os.environ.get("SLACK_CLIENT_SECRET", "mock-slack-client-secret")
SLACK_REDIRECT_URI = os.environ.get("SLACK_REDIRECT_URI", "http://localhost:8000/api/connectors/oauth/callback")

AUTH_URL = "https://slack.com/oauth/v2/authorize"
TOKEN_URL = "https://slack.com/api/oauth.v2.access"

# We request scopes necessary for discovering channels, reading messages, and downloading files
SCOPES = "channels:history,channels:read,groups:history,groups:read,im:history,im:read,mpim:history,mpim:read,users:read,users:read.email,files:read"

def get_auth_url(state: str) -> str:
    """Generate the Slack OAuth2 authorization URL."""
    return (
        f"{AUTH_URL}?client_id={SLACK_CLIENT_ID}"
        f"&user_scope={SCOPES}"
        f"&redirect_uri={SLACK_REDIRECT_URI}"
        f"&state={state}"
    )

async def exchange_code(code: str) -> Tuple[Dict[str, Any], datetime]:
    """Exchange auth code for tokens."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            TOKEN_URL,
            data={
                "client_id": SLACK_CLIENT_ID,
                "client_secret": SLACK_CLIENT_SECRET,
                "code": code,
                "redirect_uri": SLACK_REDIRECT_URI,
            }
        )
        if not response.is_success:
            raise ConnectorAuthError(f"Failed to exchange code: {response.text}")

        data = response.json()
        if not data.get("ok"):
            raise ConnectorAuthError(f"Slack OAuth error: {data.get('error')}")

        # Slack v2 returns user-level tokens inside an 'authed_user' block
        # It never expires (unless revoked or rotating is enabled, which is non-standard)
        token_data = {
            "access_token": data.get("authed_user", {}).get("access_token"),
            "provider_user_id": data.get("authed_user", {}).get("id"),
            "team_id": data.get("team", {}).get("id"),
            "team_name": data.get("team", {}).get("name"),
        }
        
        # Slack user tokens don't generally expire, but let's give it a long horizon
        expires_at = datetime.now(timezone.utc) + timedelta(days=365)
        return token_data, expires_at

async def refresh_token(refresh_token_str: str) -> Tuple[Dict[str, Any], datetime]:
    """Slack standard tokens don't expire, return sentinel."""
    return {"access_token": refresh_token_str}, datetime.now(timezone.utc) + timedelta(days=365)
