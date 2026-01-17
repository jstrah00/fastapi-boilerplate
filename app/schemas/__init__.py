"""
Pydantic schemas (DTOs) for API request/response validation.

# =============================================================================
# SCHEMAS: Define your request and response schemas here.
# Each API resource should have its own schema file.
# =============================================================================
"""
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserPasswordUpdate,
    UserResponse,
    UserListResponse,
)
from app.schemas.item import (
    ItemBase,
    ItemCreate,
    ItemUpdate,
    ItemResponse,
    ItemListResponse,
)
from app.schemas.auth import (
    Token,
    TokenPayload,
    LoginRequest,
    RefreshTokenRequest,
)

__all__ = [
    # User schemas
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserPasswordUpdate",
    "UserResponse",
    "UserListResponse",
    # Item schemas
    "ItemBase",
    "ItemCreate",
    "ItemUpdate",
    "ItemResponse",
    "ItemListResponse",
    # Auth schemas
    "Token",
    "TokenPayload",
    "LoginRequest",
    "RefreshTokenRequest",
]
