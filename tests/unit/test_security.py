"""
Unit tests for security utilities.

# =============================================================================
# EXAMPLE: Unit tests for password hashing and JWT tokens.
# =============================================================================
"""
import pytest
from datetime import timedelta

from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_password_hash_is_different_from_plain(self) -> None:
        """Hashed password should be different from plain text."""
        password = "mysecretpassword"
        hashed = get_password_hash(password)

        assert hashed != password

    def test_password_verification_success(self) -> None:
        """Correct password should verify successfully."""
        password = "mysecretpassword"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_password_verification_failure(self) -> None:
        """Wrong password should fail verification."""
        password = "mysecretpassword"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)

        assert verify_password(wrong_password, hashed) is False

    def test_different_hashes_for_same_password(self) -> None:
        """Same password should produce different hashes (due to salt)."""
        password = "mysecretpassword"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        assert hash1 != hash2
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTTokens:
    """Tests for JWT token functions."""

    def test_create_access_token(self) -> None:
        """Access token should be created successfully."""
        subject = "user-123"
        token = create_access_token(subject)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self) -> None:
        """Refresh token should be created successfully."""
        subject = "user-123"
        token = create_refresh_token(subject)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_valid_access_token(self) -> None:
        """Valid access token should decode correctly."""
        subject = "user-123"
        token = create_access_token(subject)

        payload = decode_token(token)

        assert payload is not None
        assert payload["sub"] == subject
        assert payload["type"] == "access"

    def test_decode_valid_refresh_token(self) -> None:
        """Valid refresh token should decode correctly."""
        subject = "user-123"
        token = create_refresh_token(subject)

        payload = decode_token(token)

        assert payload is not None
        assert payload["sub"] == subject
        assert payload["type"] == "refresh"

    def test_decode_invalid_token(self) -> None:
        """Invalid token should return None."""
        invalid_token = "invalid.token.here"

        payload = decode_token(invalid_token)

        assert payload is None

    def test_custom_expiration(self) -> None:
        """Token with custom expiration should decode correctly."""
        subject = "user-123"
        expires = timedelta(hours=2)
        token = create_access_token(subject, expires_delta=expires)

        payload = decode_token(token)

        assert payload is not None
        assert payload["sub"] == subject
