"""
User API endpoints with authentication and role-based permissions.

Provides CRUD operations for user management with two authorization approaches:
1. Simple admin check using CurrentAdmin dependency
2. Fine-grained RBAC using require_permissions dependency

Key components:
    - POST /users/: Create user (admin only)
    - GET /users/me: Get current user info
    - GET /users/: List all users (admin only)
    - GET /users/{id}: Get user by ID
    - PATCH /users/{id}: Update user info
    - POST /users/{id}/password: Change password
    - DELETE /users/{id}: Deactivate user (admin only)
    - PATCH /users/{id}/role: Update role/permissions (requires users:update)

Dependencies:
    - app.services.user_service: User business logic
    - app.schemas.user: Request/response schemas
    - app.api.deps: CurrentUser, CurrentAdmin, UserSvc
    - app.common.permissions: require_permissions

Related files:
    - app/services/user_service.py: Business logic
    - app/schemas/user.py: Pydantic schemas
    - app/repositories/user_repo.py: Data access
    - app/common/permissions.py: RBAC definitions

Common commands:
    - Test: uv run pytest tests/integration/ -k "user" -v
    - Try: http://localhost:8000/docs#/users

Example:
    Get current user::

        curl http://localhost:8000/api/v1/users/me \\
            -H "Authorization: Bearer <token>"

    Create user (admin)::

        curl -X POST http://localhost:8000/api/v1/users/ \\
            -H "Authorization: Bearer <admin_token>" \\
            -H "Content-Type: application/json" \\
            -d '{"email": "new@example.com", "first_name": "John", ...}'

    Update user role::

        curl -X PATCH http://localhost:8000/api/v1/users/{id}/role \\
            -H "Authorization: Bearer <token_with_users:update>" \\
            -d '{"role": "admin"}'
"""
from uuid import UUID

from fastapi import APIRouter, Depends, status, HTTPException

from app.api.deps import CurrentUser, CurrentAdmin, UserSvc, UserRepo, get_current_user
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserRoleUpdate,
    UserResponse,
    UserListResponse,
    UserPasswordUpdate,
)
from app.common.logging import get_logger
from app.common.exceptions import NotFoundError, AlreadyExistsError, ValidationError
from app.common.permissions import Permission, require_permissions
from app.models.postgres.user import User

logger = get_logger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Create a new user. Only admins can create users directly.",
)
async def create_user(
    user_data: UserCreate,
    current_user: CurrentAdmin,
    user_service: UserSvc,
) -> UserResponse:
    """Create a new user."""
    try:
        user = await user_service.create_user(user_data)
        return UserResponse.model_validate(user)
    except AlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message,
        )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get the current authenticated user's information.",
)
async def get_current_user_info(
    current_user: CurrentUser,
) -> UserResponse:
    """Get current user information."""
    return UserResponse.model_validate(current_user)


@router.get(
    "/",
    response_model=UserListResponse,
    summary="List users",
    description="List all users. Only admins can list all users.",
)
async def list_users(
    current_user: CurrentAdmin,
    user_repo: UserRepo,
    skip: int = 0,
    limit: int = 100,
) -> UserListResponse:
    """List all users with pagination."""
    users = await user_repo.get_all(skip=skip, limit=limit)
    total = await user_repo.count()

    return UserListResponse(
        users=[UserResponse.model_validate(u) for u in users],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
    description="Get a specific user by ID.",
)
async def get_user(
    user_id: UUID,
    current_user: CurrentUser,
    user_service: UserSvc,
) -> UserResponse:
    """Get user by ID."""
    # Users can only see themselves unless they're admin
    if user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own profile",
        )

    try:
        user = await user_service.get_user_by_id(user_id)
        return UserResponse.model_validate(user)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user",
    description="Update user information. Users can update themselves, admins can update anyone.",
)
async def update_user(
    user_id: UUID,
    update_data: UserUpdate,
    current_user: CurrentUser,
    user_service: UserSvc,
) -> UserResponse:
    """Update user information."""
    try:
        user = await user_service.update_user(user_id, update_data, current_user)
        return UserResponse.model_validate(user)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.message,
        )


@router.post(
    "/{user_id}/password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change password",
    description="Change user password. Requires current password.",
)
async def change_password(
    user_id: UUID,
    password_data: UserPasswordUpdate,
    current_user: CurrentUser,
    user_service: UserSvc,
) -> None:
    """Change user password."""
    # Users can only change their own password
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only change your own password",
        )

    try:
        await user_service.change_password(
            user_id,
            password_data.current_password,
            password_data.new_password,
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate user",
    description="Deactivate (soft delete) a user. Only admins can deactivate users.",
)
async def deactivate_user(
    user_id: UUID,
    current_user: CurrentAdmin,
    user_service: UserSvc,
) -> None:
    """Deactivate a user."""
    try:
        await user_service.deactivate_user(user_id, current_user)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )


# =============================================================================
# Role & Permission Management
# =============================================================================

@router.patch(
    "/{user_id}/role",
    response_model=UserResponse,
    summary="Update user role",
    description="""
    Update user role and/or custom permissions.

    **Requires:** `users:update` permission

    **Example usage:**
    - Change role: `{"role": "admin"}`
    - Add custom permissions: `{"custom_permissions": ["items:delete"]}`
    - Both: `{"role": "user", "custom_permissions": ["users:read"]}`
    """,
)
async def update_user_role(
    user_id: UUID,
    role_data: UserRoleUpdate,
    user_service: UserSvc,
    # EXAMPLE: Using require_permissions for fine-grained access control
    # This allows any user with USERS_UPDATE permission (not just admins)
    current_user: User = Depends(require_permissions(Permission.USERS_UPDATE)),
) -> UserResponse:
    """
    Update user role and permissions.

    This endpoint demonstrates the require_permissions dependency.
    """
    try:
        user = await user_service.update_user_role(user_id, role_data, current_user)
        return UserResponse.model_validate(user)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.message,
        )
