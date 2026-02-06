"""
Role-based access control (RBAC) system.

Provides a flexible permission system with granular permissions, role definitions,
and FastAPI dependencies for enforcing access control in endpoints.

Key components:
    - Permission: Enum of all available permissions (e.g., USERS_READ, ITEMS_CREATE)
    - Role: Enum of user roles (e.g., ADMIN, USER)
    - ROLE_PERMISSIONS: Mapping of roles to their permission sets
    - require_permissions: FastAPI dependency requiring ALL listed permissions
    - require_any_permission: FastAPI dependency requiring ANY listed permission
    - require_admin: Convenience dependency for admin-only routes
    - get_user_permissions: Get combined role + custom permissions for a user
    - has_permission: Check if a user has a specific permission

Dependencies:
    - fastapi: Depends, HTTPException for dependency injection
    - app.api.deps: get_current_user (imported at runtime to avoid circular import)

Related files:
    - app/api/deps.py: CurrentUser, get_current_user dependencies
    - app/models/postgres/user.py: User.role and User.custom_permissions fields
    - app/schemas/user.py: UserCreate, UserRoleUpdate with role validation
    - app/api/v1/users.py: Example usage in endpoints

Common commands:
    - Test: uv run pytest tests/ -k "permission"

Example:
    Using in endpoints::

        from app.common.permissions import Permission, require_permissions

        @router.delete("/users/{user_id}")
        async def delete_user(
            user_id: UUID,
            current_user: User = Depends(require_permissions(
                Permission.USERS_READ,
                Permission.USERS_DELETE
            ))
        ):
            # Only users with BOTH permissions can access
            ...

    Checking permissions in service layer::

        from app.common.permissions import has_permission, Permission

        if has_permission(user.role, Permission.ITEMS_DELETE, user.custom_permissions):
            # User can delete items
            ...
"""
from enum import Enum
from typing import Callable

from fastapi import Depends, HTTPException, status

from app.common.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# Permission Definitions
# =============================================================================

class Permission(str, Enum):
    """
    Permission definitions for the application.

    CUSTOMIZATION: Add new permissions as needed for your application.
    Use format: RESOURCE_ACTION (e.g., USERS_READ, ITEMS_DELETE)

    Examples of common permissions you might add:
    - REPORTS_GENERATE = "reports:generate"
    - SETTINGS_MANAGE = "settings:manage"
    - BILLING_VIEW = "billing:view"
    """

    # User management permissions
    USERS_READ = "users:read"
    USERS_CREATE = "users:create"
    USERS_UPDATE = "users:update"
    USERS_DELETE = "users:delete"

    # Item/Resource permissions (example - customize for your domain)
    ITEMS_READ = "items:read"
    ITEMS_CREATE = "items:create"
    ITEMS_UPDATE = "items:update"
    ITEMS_DELETE = "items:delete"

    # Admin permissions
    ADMIN_ACCESS = "admin:access"
    ADMIN_SETTINGS = "admin:settings"

    # Add your custom permissions here:
    # EXAMPLE_PERMISSION = "example:action"


# =============================================================================
# Role Definitions
# =============================================================================

class Role(str, Enum):
    """
    Role definitions for the application.

    CUSTOMIZATION: Add new roles as needed. Each role should have a
    corresponding entry in ROLE_PERMISSIONS defining its permissions.

    Examples of roles you might add:
    - MANAGER = "manager"
    - MODERATOR = "moderator"
    - VIEWER = "viewer"
    """

    ADMIN = "admin"
    USER = "user"
    # Add custom roles here:
    # MANAGER = "manager"
    # MODERATOR = "moderator"


# Role to permissions mapping
# CUSTOMIZATION: Define which permissions each role has
ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    # Admin role - has all permissions
    Role.ADMIN: {
        Permission.USERS_READ,
        Permission.USERS_CREATE,
        Permission.USERS_UPDATE,
        Permission.USERS_DELETE,
        Permission.ITEMS_READ,
        Permission.ITEMS_CREATE,
        Permission.ITEMS_UPDATE,
        Permission.ITEMS_DELETE,
        Permission.ADMIN_ACCESS,
        Permission.ADMIN_SETTINGS,
    },

    # Regular user role - limited permissions
    Role.USER: {
        Permission.ITEMS_READ,
        Permission.ITEMS_CREATE,
        Permission.ITEMS_UPDATE,
        # Users can't delete items or access admin features
    },

    # Add permissions for custom roles:
    # Role.MANAGER: {
    #     Permission.USERS_READ,
    #     Permission.ITEMS_READ,
    #     Permission.ITEMS_CREATE,
    #     Permission.ITEMS_UPDATE,
    #     Permission.ITEMS_DELETE,
    # },
}


# =============================================================================
# Permission Checking Functions
# =============================================================================

def get_user_permissions(role: str, custom_permissions: list[str] | None = None) -> set[Permission]:
    """
    Get all permissions for a user based on their role and custom permissions.

    Args:
        role: User's role (should match a Role enum value)
        custom_permissions: Optional list of additional permission strings

    Returns:
        Set of Permission enums the user has

    Example:
        permissions = get_user_permissions("admin")
        if Permission.USERS_DELETE in permissions:
            # User can delete users
    """
    permissions: set[Permission] = set()

    # Get permissions from role
    try:
        role_enum = Role(role)
        permissions = ROLE_PERMISSIONS.get(role_enum, set()).copy()
    except ValueError:
        logger.warning("unknown_role", role=role)

    # Add custom permissions if provided
    if custom_permissions:
        for perm_str in custom_permissions:
            try:
                perm = Permission(perm_str)
                permissions.add(perm)
            except ValueError:
                logger.warning("unknown_permission", permission=perm_str)

    return permissions


def has_permission(
    role: str,
    required_permission: Permission,
    custom_permissions: list[str] | None = None,
) -> bool:
    """
    Check if a user with given role has a specific permission.

    Args:
        role: User's role
        required_permission: The permission to check for
        custom_permissions: Optional list of additional permission strings

    Returns:
        True if user has the permission, False otherwise
    """
    user_permissions = get_user_permissions(role, custom_permissions)
    return required_permission in user_permissions


def has_all_permissions(
    role: str,
    required_permissions: list[Permission],
    custom_permissions: list[str] | None = None,
) -> bool:
    """
    Check if a user has ALL of the required permissions.

    Args:
        role: User's role
        required_permissions: List of permissions to check
        custom_permissions: Optional list of additional permission strings

    Returns:
        True if user has all permissions, False otherwise
    """
    user_permissions = get_user_permissions(role, custom_permissions)
    return all(perm in user_permissions for perm in required_permissions)


def has_any_permission(
    role: str,
    required_permissions: list[Permission],
    custom_permissions: list[str] | None = None,
) -> bool:
    """
    Check if a user has ANY of the required permissions.

    Args:
        role: User's role
        required_permissions: List of permissions to check
        custom_permissions: Optional list of additional permission strings

    Returns:
        True if user has at least one permission, False otherwise
    """
    user_permissions = get_user_permissions(role, custom_permissions)
    return any(perm in user_permissions for perm in required_permissions)


# =============================================================================
# FastAPI Dependencies
# =============================================================================

def require_permissions(*permissions: Permission) -> Callable:
    """
    FastAPI dependency that requires specific permissions.

    This dependency should be used after get_current_user to verify
    that the authenticated user has the required permissions.

    Args:
        *permissions: Variable number of Permission enums required

    Returns:
        Dependency function that validates permissions

    Example:
        @router.delete("/users/{user_id}")
        async def delete_user(
            user_id: UUID,
            current_user: User = Depends(require_permissions(
                Permission.USERS_READ,
                Permission.USERS_DELETE
            ))
        ):
            ...

    NOTE: This dependency imports get_current_user from app.api.deps
    to avoid circular imports. Make sure get_current_user is defined
    in your deps module.
    """
    async def permission_checker(
        # Import here to avoid circular dependency
        current_user: "User" = Depends(get_current_user_dependency()),
    ) -> "User":
        # Get user's permissions based on role
        user_permissions = get_user_permissions(
            current_user.role,
            current_user.custom_permissions,
        )

        # Check if user has all required permissions
        missing = [p for p in permissions if p not in user_permissions]

        if missing:
            logger.warning(
                "permission_denied",
                user_id=str(current_user.id),
                required=list(permissions),
                missing=missing,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permissions: {', '.join(str(p.value) for p in missing)}",
            )

        return current_user

    return permission_checker


def require_any_permission(*permissions: Permission) -> Callable:
    """
    FastAPI dependency that requires at least one of the specified permissions.

    Similar to require_permissions but only requires ONE of the permissions.

    Args:
        *permissions: Variable number of Permission enums (at least one required)

    Returns:
        Dependency function that validates permissions

    Example:
        @router.get("/reports")
        async def view_reports(
            current_user: User = Depends(require_any_permission(
                Permission.ADMIN_ACCESS,
                Permission.REPORTS_GENERATE
            ))
        ):
            ...
    """
    async def permission_checker(
        current_user: "User" = Depends(get_current_user_dependency()),
    ) -> "User":
        user_permissions = get_user_permissions(
            current_user.role,
            current_user.custom_permissions,
        )

        if not any(p in user_permissions for p in permissions):
            logger.warning(
                "permission_denied",
                user_id=str(current_user.id),
                required_any=list(permissions),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to perform this action",
            )

        return current_user

    return permission_checker


def require_admin() -> Callable:
    """
    FastAPI dependency that requires admin role.

    Convenience dependency for admin-only routes.

    Example:
        @router.get("/admin/dashboard")
        async def admin_dashboard(
            current_user: User = Depends(require_admin())
        ):
            ...
    """
    return require_permissions(Permission.ADMIN_ACCESS)


# Helper to get the current user dependency without circular imports
def get_current_user_dependency() -> Callable:
    """
    Returns the get_current_user dependency.

    This function exists to avoid circular imports between
    permissions.py and deps.py.
    """
    from app.api.deps import get_current_user
    return get_current_user


# Type hint for User model (to avoid import)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.postgres.user import User
