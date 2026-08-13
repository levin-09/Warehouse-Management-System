"""Authentication and authorization helpers for the Whitfield WMS backend.

Provides JWT creation/decoding and password hashing. Tokens carry the user id,
email, role, and warehouse scope so routes and controllers can enforce role-based
access without an extra database round trip.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
from jose import JWTError, jwt

from core.config import settings


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt.

    Uses the raw ``bcrypt`` library rather than passlib to avoid the passlib/bcrypt
    4.x version-detection incompatibility. Emits ``$2b$``-prefixed hashes, which are
    compatible with passlib-generated hashes.

    Args:
        password: Plaintext password.

    Returns:
        str: bcrypt hash.
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash.

    Args:
        plain_password: Plaintext candidate.
        hashed_password: Stored bcrypt hash.

    Returns:
        bool: True if the password matches, False on mismatch or bad input.
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False


def create_access_token(data: Dict[str, Any], expires_minutes: Optional[int] = None) -> str:
    """Create a signed JWT access token.

    Args:
        data: Claims to embed (id, email, role, warehouse_id).
        expires_minutes: Token lifetime override; defaults to settings value.

    Returns:
        str: Encoded JWT string.
    """
    to_encode = dict(data)
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.access_token_expire_minutes
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_jwt(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT access token.

    Args:
        token: Bearer token string.

    Returns:
        Optional[dict]: Decoded claims, or None if the token is invalid/expired.
    """
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
