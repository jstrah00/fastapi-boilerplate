"""
Pydantic schemas for User API endpoints.

Defines request/response DTOs (Data Transfer Objects) for user-related API
operations including creation, updates, and responses.

Key components:
    - UserBase: Common fields shared across schemas
    - UserCreate: Request schema for creating users
    - UserUpdate: Request schema for updating user info
    - UserRoleUpdate: Request schema for updating role/permissions
    - UserPasswordUpdate: Request schema for changing password
    - UserResponse: Response schema with user data (no password)
    - UserListResponse: Paginated list response

Dependencies:
    - pydantic: Data validation and serialization
    - email-validator: Email validation

Related files:
    - app/models/postgres/user.py: User model these schemas map to
    - app/services/user_service.py: Uses these for input validation
    - app/api/v1/users.py: API endpoints using these schemas

Common commands:
    - Test validation: Use Swagger UI at /docs to test request bodies

Example:
    Creating a user via API::

        # POST /api/v1/users/
        {
            "email": "user@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "password": "securepassword123",
            "role": "user"
        }

    Response::

        {
            "id": "uuid-here",
            "email": "user@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "status": "active",
            "role": "user",
            "is_admin": false,
            "permissions": ["items:read", "items:create", "items:update"],
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:30:00Z"
        }
"""
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict, computed_field

if TYPE_CHECKING:
    from app.models.postgres.user import User


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
    The 'permissions' field contains all effective permissions
    (combining role-based + custom permissions).
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    role: str
    custom_permissions: list[str] | None = None
    is_admin: bool  # Computed property from role
    created_at: datetime
    updated_at: datetime

    @computed_field  # type: ignore[misc]
    @property
    def permissions(self) -> list[str]:
        """
        Get all effective permissions for this user.

        Combines role-based permissions with custom permissions.
        This field is computed dynamically and sent to frontend for
        client-side permission checks.

        Returns:
            List of permission strings (e.g., ["users:read", "items:create"])
        """
        from app.common.permissions import get_user_permissions

        user_perms = get_user_permissions(self.role, self.custom_permissions)
        return sorted([perm.value for perm in user_perms])


class UserListResponse(BaseModel):
    """Schema for paginated user list."""

    users: list[UserResponse]
    total: int
    skip: int
    limit: int
