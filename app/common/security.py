"""
Security utilities for authentication.

Provides JWT token creation/validation and password hashing using industry-standard
algorithms (bcrypt for passwords, HS256 for JWTs).

Key components:
    - get_password_hash: Hash a plain password with bcrypt
    - verify_password: Verify a password against its hash
    - create_access_token: Generate JWT access token (short-lived)
    - create_refresh_token: Generate JWT refresh token (long-lived)
    - decode_token: Decode and validate a JWT token

Dependencies:
    - python-jose[cryptography]: JWT encoding/decoding
    - passlib[bcrypt]: Password hashing
    - app.config: SECRET_KEY, token expiration settings

Related files:
    - app/config.py: SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES, etc.
    - app/services/auth_service.py: Uses these for login/refresh
    - app/api/deps.py: Uses decode_token for authentication

Common commands:
    - Generate secret: python -c "import secrets; print(secrets.token_hex(32))"
    - Test: uv run pytest tests/unit/test_security.py -v

Example:
    Password hashing::

        from app.common.security import get_password_hash, verify_password

        hashed = get_password_hash("mypassword123")
        is_valid = verify_password("mypassword123", hashed)  # True

    Token creation::

        from app.common.security import create_access_token, decode_token

        token = create_access_token(subject=str(user.id))
        payload = decode_token(token)
        user_id = payload["sub"]  # UUID string
"""
from datetime import datetime, timedelta, UTC
from typing import Any

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.config import settings
from app.common.logging import get_logger

logger = get_logger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# =============================================================================
# Password Hashing
# =============================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password: The plain text password
        hashed_password: The hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: The plain text password

    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


# =============================================================================
# JWT Token Management
# =============================================================================

def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        subject: Token subject (usually user ID)
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token
    """
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {
        "sub": subject,
        "exp": expire,
        "type": "access",
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    logger.debug("access_token_created", subject=subject)

    return encoded_jwt


def create_refresh_token(
    subject: str,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a JWT refresh token.

    Args:
        subject: Token subject (usually user ID)
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token
    """
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

    to_encode = {
        "sub": subject,
        "exp": expire,
        "type": "refresh",
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    logger.debug("refresh_token_created", subject=subject)

    return encoded_jwt


def decode_token(token: str) -> dict[str, Any] | None:
    """
    Decode and validate a JWT token.

    Args:
        token: The JWT token to decode

    Returns:
        Token payload if valid, None if invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError as e:
        logger.debug("token_decode_failed", error=str(e))
        return None
