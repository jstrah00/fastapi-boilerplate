"""
Security utilities for authentication.

# =============================================================================
# SECURITY: JWT token handling and password hashing.
# =============================================================================
"""
from datetime import datetime, timedelta, UTC
from typing import Any

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.config import settings
from app.core.logging import get_logger

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
