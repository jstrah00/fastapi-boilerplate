"""
Pydantic schemas for authentication endpoints.

# =============================================================================
# AUTH SCHEMAS: Token and login DTOs.
# =============================================================================
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
