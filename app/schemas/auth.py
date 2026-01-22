"""
Pydantic schemas for authentication endpoints.

Defines request/response DTOs for authentication operations including
login, token refresh, and JWT token structure.

Key components:
    - LoginRequest: Email and password for login
    - Token: Access and refresh token response
    - TokenPayload: Decoded JWT token structure
    - RefreshTokenRequest: Refresh token for getting new access token

Dependencies:
    - pydantic: Data validation and serialization
    - email-validator: Email validation

Related files:
    - app/services/auth_service.py: Authentication business logic
    - app/api/v1/auth.py: Authentication endpoints
    - app/common/security.py: Token creation and validation

Common commands:
    - Test: uv run pytest tests/integration/test_auth.py -v

Example:
    Login request::

        # POST /api/v1/auth/login
        {
            "email": "user@example.com",
            "password": "password123"
        }

    Token response::

        {
            "access_token": "eyJ...",
            "refresh_token": "eyJ...",
            "token_type": "bearer"
        }

    Refresh token::

        # POST /api/v1/auth/refresh
        {
            "refresh_token": "eyJ..."
        }
"""
from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    """Schema for access token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Schema for token payload (decoded JWT)."""

    sub: str  # Subject (user_id)
    exp: int  # Expiration time
    type: str  # Token type (access or refresh)


class LoginRequest(BaseModel):
    """Schema for login request."""

    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""

    refresh_token: str
