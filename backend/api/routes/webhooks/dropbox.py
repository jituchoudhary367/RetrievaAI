"""
Dropbox Webhook Receiver
------------------------
Handles the two types of requests Dropbox sends to a webhook endpoint:

1. GET verification challenge:
   Dropbox sends a `challenge` query param. We must echo it back with
   Content-Type: text/plain and X-Content-Type-Options: nosniff.

2. POST notifications:
   Dropbox sends a JSON body listing which account UIDs have changes.
   We MUST verify the HMAC-SHA256 signature in X-Dropbox-Signature
   before doing anything with the payload.

After signature verification, we enqueue an incremental sync task
for each affected connection (looked up by the Dropbox account UID).
"""

import hashlib
import hmac
import logging
import os
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Request, Response

logger = logging.getLogger(__name__)

router = APIRouter()

DROPBOX_APP_SECRET = os.environ.get("DROPBOX_APP_SECRET", "mock-dropbox-app-secret")


def _verify_signature(body: bytes, signature_header: str) -> bool:
    """
    Verify the Dropbox webhook HMAC-SHA256 signature.

    Dropbox signs the raw request body with the app secret and puts the
    hex digest in the X-Dropbox-Signature header.

    Returns True if the signature is valid, False otherwise.
    """
    if not signature_header:
        return False

    expected = hmac.new(
        DROPBOX_APP_SECRET.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()

    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(expected, signature_header)


@router.get("/webhooks/dropbox")
async def dropbox_verify_challenge(challenge: str) -> Response:
    """
    Handle Dropbox's one-time challenge verification request.
    Dropbox sends this when the webhook URL is first registered.
    """
    return Response(
        content=challenge,
        media_type="text/plain",
        headers={"X-Content-Type-Options": "nosniff"},
    )


@router.post("/webhooks/dropbox")
async def dropbox_receive_notification(request: Request) -> Dict[str, Any]:
    """
    Handle Dropbox webhook notification.

    Dropbox will POST JSON like:
    {
        "list_folder": {
            "accounts": ["dbid:abc123", "dbid:def456"]
        },
        "delta": {
            "users": [12345678]
        }
    }

    We verify the signature, then enqueue incremental sync tasks for
    each account that has changes.
    """
    body = await request.body()

    # --- SIGNATURE VERIFICATION (mandatory, per spec) ---
    signature_header = request.headers.get("X-Dropbox-Signature", "")
    if not _verify_signature(body, signature_header):
        logger.warning("Dropbox webhook: invalid signature rejected")
        raise HTTPException(status_code=403, detail="Invalid Dropbox signature")

    # --- Parse payload ---
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    affected_accounts: List[str] = (
        payload.get("list_folder", {}).get("accounts", [])
    )

    if not affected_accounts:
        logger.debug("Dropbox webhook: no affected accounts in payload")
        return {"status": "ok", "queued": 0}

    queued = 0
    for account_id in affected_accounts:
        try:
            # Import lazily to avoid circular imports at module load time
            from tasks.sync_tasks import sync_connector_task  # type: ignore

            # Look up the connector connection by provider_user_id
            # The task itself resolves the connection and runs incremental sync
            sync_connector_task.delay(
                provider="dropbox",
                provider_user_id=account_id,
                sync_type="incremental",
            )
            queued += 1
            logger.info(f"Dropbox webhook: queued incremental sync for account {account_id}")
        except Exception as exc:
            # Log but don't fail — Dropbox retries if we return non-2xx
            logger.error(f"Failed to enqueue sync for Dropbox account {account_id}: {exc}")

    return {"status": "ok", "queued": queued}
