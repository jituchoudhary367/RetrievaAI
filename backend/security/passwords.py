"""
security/passwords.py

Password hashing and verification using passlib.
"""

import bcrypt

def hash_password(plain: str) -> str:
    """Hash a plain text password."""
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(plain.encode('utf-8'), salt)
    return hashed_bytes.decode('utf-8')

def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain text password against its hash."""
    return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
