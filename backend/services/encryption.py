"""
services/encryption.py

AES-256-GCM encryption/decryption for sensitive data at rest.

Used by the workspace provider service to encrypt API keys before
storing them in the database.

Key derivation:
  PBKDF2-HMAC-SHA256(SECURITY_JWT_SECRET_KEY, salt=b'workspace-keys', iterations=200_000)
  → 32-byte AES key

This reuses the existing JWT secret — no new environment variable required.

Usage:
    from services.encryption import encrypt, decrypt

    ct = encrypt("sk-abc123...")
    pt = decrypt(ct)  # → "sk-abc123..."
"""

from __future__ import annotations

import base64
import hashlib
import os
import struct
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Lazy import so the module is importable even if cryptography isn't installed
_HAVE_CRYPTOGRAPHY = False
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore
    _HAVE_CRYPTOGRAPHY = True
except ImportError:
    pass


def _derive_key() -> bytes:
    """Derive a 32-byte AES key from SECURITY_JWT_SECRET_KEY."""
    from app.config import get_settings
    secret = get_settings().security.jwt_secret_key or "dev-secret-change-in-production"
    return hashlib.pbkdf2_hmac(
        "sha256",
        secret.encode(),
        b"workspace-provider-keys",
        iterations=200_000,
        dklen=32,
    )


def encrypt(plaintext: str) -> str:
    """
    Encrypt *plaintext* using AES-256-GCM.

    Returns a base64-encoded string: nonce(12) + ciphertext + tag.
    Falls back to base64-only encoding if cryptography isn't installed
    (logs a warning in that case).
    """
    if not plaintext:
        return ""

    if not _HAVE_CRYPTOGRAPHY:
        logger.warning(
            "cryptography package not installed. API keys stored without encryption. "
            "Install with: pip install cryptography"
        )
        return base64.b64encode(plaintext.encode()).decode()

    key = _derive_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
    payload = nonce + ct
    return base64.b64encode(payload).decode()


def decrypt(ciphertext: str) -> str:
    """
    Decrypt a value previously produced by :func:`encrypt`.

    Returns empty string on any error (e.g. key rotation, corrupt data).
    """
    if not ciphertext:
        return ""

    if not _HAVE_CRYPTOGRAPHY:
        try:
            return base64.b64decode(ciphertext).decode()
        except Exception:
            return ""

    try:
        payload = base64.b64decode(ciphertext)
        nonce, ct = payload[:12], payload[12:]
        key = _derive_key()
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ct, None).decode()
    except Exception as exc:
        logger.warning("Decryption failed: %s", exc)
        return ""


def mask(value: str) -> str:
    """Return a masked version of a secret for display (e.g. 'sk-ab...cd12')."""
    if not value or len(value) < 8:
        return "***"
    return value[:4] + "..." + value[-4:]


__all__ = ["encrypt", "decrypt", "mask"]
