"""
Pydantic schemas for User API endpoints.

Defines request/response DTOs for user-related API operations including
creation, updates, and responses for the A2W platform.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict, computed_field


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
    """Schema for creating a new user (admin action)."""

    password: str = Field(min_length=8, max_length=100)
    role: str = Field(default="aretan", pattern="^(admin|aretan|contratante)$")
    custom_permissions: list[str] | None = None


class UserUpdate(BaseModel):
    """Schema for updating user information."""

    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    status: str | None = Field(
        None, pattern="^(pending|active|inactive|rejected|blocked)$"
    )


class UserRoleUpdate(BaseModel):
    """Schema for updating user role and permissions (admin only)."""

    role: str | None = Field(None, pattern="^(admin|aretan|contratante)$")
    custom_permissions: list[str] | None = None


class UserPasswordUpdate(BaseModel):
    """Schema for updating user password."""

    current_password: str
    new_password: str = Field(min_length=8, max_length=16)


class UserApprovalAction(BaseModel):
    """Schema for approving or rejecting an Aretan user."""

    action: str = Field(pattern="^(approve|reject)$")


# =============================================================================
# Response Schemas
# =============================================================================

class UserResponse(UserBase):
    """Schema for user response (without sensitive data)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    role: str
    avatar_url: str | None = None
    phone: str | None = None
    country: str | None = None
    custom_permissions: list[str] | None = None
    email_notifications_enabled: bool = True
    is_admin: bool
    created_at: datetime
    updated_at: datetime

    @computed_field  # type: ignore[misc]
    @property
    def permissions(self) -> list[str]:
        """Get all effective permissions for this user."""
        from app.common.permissions import get_user_permissions

        user_perms = get_user_permissions(self.role, self.custom_permissions)
        return sorted([perm.value for perm in user_perms])


class UserListResponse(BaseModel):
    """Schema for paginated user list."""

    users: list[UserResponse]
    total: int
    skip: int
    limit: int
