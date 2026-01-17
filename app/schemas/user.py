"""
Pydantic schemas for User API endpoints.

# =============================================================================
# SCHEMAS: Request/Response DTOs for the User API.
# Customize these based on your authentication requirements.
# =============================================================================
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict


# =============================================================================
# Base Schemas
# =============================================================================

class UserBase(BaseModel):
    """Base user schema with common fields."""

    email: EmailStr
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)


# =============================================================================
# Request Schemas
# =============================================================================

class UserCreate(UserBase):
    """
    Schema for creating a new user.

    CUSTOMIZATION: Add or remove fields based on your registration requirements.
    """

    password: str = Field(min_length=8, max_length=100)

    # Role assignment - defaults to "user"
    # Valid values should match Role enum in app/core/permissions.py
    role: str = Field(default="user", pattern="^(admin|user)$")

    # Optional custom permissions beyond role defaults
    # Values should match Permission enum in app/core/permissions.py
    custom_permissions: list[str] | None = None


class UserUpdate(BaseModel):
    """
    Schema for updating user information.

    All fields are optional - only provided fields will be updated.
    """

    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    status: str | None = Field(None, pattern="^(active|inactive)$")


class UserRoleUpdate(BaseModel):
    """
    Schema for updating user role and permissions.

    ADMIN ONLY: Use this to change user roles and grant/revoke permissions.
    """

    role: str | None = Field(None, pattern="^(admin|user)$")
    custom_permissions: list[str] | None = None


class UserPasswordUpdate(BaseModel):
    """Schema for updating user password."""

    current_password: str
    new_password: str = Field(min_length=8, max_length=100)


# =============================================================================
# Response Schemas
# =============================================================================

class UserResponse(UserBase):
    """
    Schema for user response (without sensitive data).

    Includes role and permissions for frontend authorization.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    role: str
    custom_permissions: list[str] | None = None
    is_admin: bool  # Computed property from role
    created_at: datetime
    updated_at: datetime


class UserListResponse(BaseModel):
    """Schema for paginated user list."""

    users: list[UserResponse]
    total: int
    skip: int
    limit: int
