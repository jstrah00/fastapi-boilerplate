"""
User service with business logic.

Contains business logic for user management operations including CRUD,
password changes, and role management with proper authorization checks.

Key components:
    - UserService: Service class for user operations
    - get_user_by_id: Retrieve user with not-found handling
    - get_user_by_email: Retrieve user by email
    - create_user: Create new user with duplicate check
    - update_user: Update user info with authorization
    - change_password: Change password with current password verification
    - deactivate_user: Soft delete user (admin only)
    - update_user_role: Update role and permissions (requires USERS_UPDATE)

Dependencies:
    - app.repositories.user_repo: User data access
    - app.common.security: Password hashing
    - app.common.exceptions: Business error types
    - app.common.permissions: Permission checking

Related files:
    - app/api/v1/users.py: User API endpoints
    - app/repositories/user_repo.py: Data access layer
    - app/schemas/user.py: Request/response schemas
    - app/common/permissions.py: RBAC definitions

Common commands:
    - Test: uv run pytest tests/ -k "user"

Example:
    Creating a user::

        user_service = UserService(user_repo)

        user = await user_service.create_user(UserCreate(
            email="new@example.com",
            first_name="John",
            last_name="Doe",
            password="secure123",
            role="user"
        ))
        # Raises AlreadyExistsError if email taken

    Updating with authorization::

        updated = await user_service.update_user(
            user_id=target_id,
            update_data=UserUpdate(first_name="Jane"),
            current_user=requesting_user  # Must be self or admin
        )

    Password change::

        await user_service.change_password(
            user_id=user.id,
            current_password="oldpass",
            new_password="newpass"
        )
        # Raises ValidationError if current_password is wrong
"""
from uuid import UUID

from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repo import UserRepository
from app.models.postgres.user import User
from app.models.postgres.post import Post
from app.models.postgres.comment import Comment
from app.schemas.user import UserCreate, UserUpdate, UserRoleUpdate
from app.common.security import get_password_hash, verify_password
from app.common.logging import get_logger
from app.common.exceptions import (
    NotFoundError,
    AlreadyExistsError,
    ValidationError,
)
from app.common.permissions import Permission, has_permission
from app.services import email_service

logger = get_logger(__name__)


class UserService:
    """
    Service for user business logic.

    # EXAMPLE: Shows service layer pattern with:
    # - Input validation
    # - Business rules enforcement
    # - Repository delegation
    """

    def __init__(self, user_repo: UserRepository, db: AsyncSession | None = None):
        self.user_repo = user_repo
        self.db = db

    async def get_user_by_id(self, user_id: UUID) -> User:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User object

        Raises:
            NotFoundError: If user not found
        """
        user = await self.user_repo.get(user_id)
        if not user:
            logger.warning("user_not_found", user_id=str(user_id))
            raise NotFoundError(
                message="User not found",
                details={"user_id": str(user_id)},
            )
        return user

    async def get_user_by_email(self, email: str) -> User:
        """
        Get user by email.

        Args:
            email: User email

        Returns:
            User object

        Raises:
            NotFoundError: If user not found
        """
        user = await self.user_repo.get_by_email(email)
        if not user:
            logger.warning("user_not_found_by_email", email=email)
            raise NotFoundError(
                message="User not found",
                details={"email": email},
            )
        return user

    async def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user.

        Args:
            user_data: User creation data

        Returns:
            Created user

        Raises:
            AlreadyExistsError: If user with email already exists
        """
        # Check if user already exists
        existing = await self.user_repo.get_by_email(user_data.email)
        if existing:
            logger.warning("user_already_exists", email=user_data.email)
            raise AlreadyExistsError(
                message="User with this email already exists",
                details={"email": user_data.email},
            )

        # Create user
        user = User(
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            password_hash=get_password_hash(user_data.password),
            role=user_data.role,
            custom_permissions=user_data.custom_permissions,
            status="active",
        )

        created_user = await self.user_repo.create(user)

        logger.info(
            "user_created",
            user_id=str(created_user.id),
            email=created_user.email,
            role=created_user.role,
        )

        return created_user

    async def update_user(
        self,
        user_id: UUID,
        update_data: UserUpdate,
        current_user: User,
    ) -> User:
        """
        Update user information.

        Args:
            user_id: User ID to update
            update_data: Update data
            current_user: User performing the update

        Returns:
            Updated user

        Raises:
            NotFoundError: If user not found
            ValidationError: If user doesn't have permission
        """
        # Get current status before update for block/unblock detection
        target_user = await self.get_user_by_id(user_id)
        old_status = target_user.status

        # Check permissions (user can update themselves, or admin can update anyone)
        if user_id != current_user.id and not current_user.is_admin:
            raise ValidationError(
                message="You don't have permission to update this user",
                details={"user_id": str(user_id)},
            )

        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        updated_user = await self.user_repo.update(user_id, update_dict)

        if not updated_user:
            raise NotFoundError(
                message="User not found",
                details={"user_id": str(user_id)},
            )

        # Auto-hide/show posts and comments when user is blocked/unblocked
        new_status = update_dict.get("status")
        if new_status and new_status != old_status and self.db:
            if new_status == "blocked":
                await self._toggle_user_content(user_id, hidden=True)
            elif new_status == "active" and old_status == "blocked":
                await self._toggle_user_content(user_id, hidden=False)

        logger.info(
            "user_updated",
            user_id=str(user_id),
            updated_fields=list(update_dict.keys()),
            updated_by=str(current_user.id),
        )

        return updated_user

    async def change_password(
        self,
        user_id: UUID,
        current_password: str,
        new_password: str,
    ) -> User:
        """
        Change user password.

        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password

        Returns:
            Updated user

        Raises:
            NotFoundError: If user not found
            ValidationError: If current password is incorrect
        """
        user = await self.get_user_by_id(user_id)

        # Verify current password
        if not verify_password(current_password, user.password_hash):
            logger.warning(
                "password_change_failed",
                user_id=str(user_id),
                reason="incorrect_current_password",
            )
            raise ValidationError(
                message="Current password is incorrect",
                details={"user_id": str(user_id)},
            )

        # Update password
        new_hash = get_password_hash(new_password)
        updated_user = await self.user_repo.update(
            user_id,
            {"password_hash": new_hash},
        )

        if not updated_user:
            raise NotFoundError(
                message="User not found",
                details={"user_id": str(user_id)},
            )

        logger.info("password_changed", user_id=str(user_id))

        return updated_user

    async def deactivate_user(
        self,
        user_id: UUID,
        current_user: User,
    ) -> User:
        """
        Deactivate a user (soft delete).

        Args:
            user_id: User ID
            current_user: User performing the deactivation

        Returns:
            Deactivated user

        Raises:
            NotFoundError: If user not found
            ValidationError: If user doesn't have permission
        """
        # Only admins can deactivate users
        if not current_user.is_admin:
            raise ValidationError(
                message="Only admins can deactivate users",
                details={"user_id": str(user_id)},
            )

        # Deactivate
        deactivated_user = await self.user_repo.soft_delete(user_id)

        if not deactivated_user:
            raise NotFoundError(
                message="User not found",
                details={"user_id": str(user_id)},
            )

        logger.info(
            "user_deactivated",
            user_id=str(user_id),
            deactivated_by=str(current_user.id),
        )

        return deactivated_user

    async def update_user_role(
        self,
        user_id: UUID,
        role_data: UserRoleUpdate,
        current_user: User,
    ) -> User:
        """
        Update user role and/or custom permissions.

        Args:
            user_id: User ID to update
            role_data: Role update data
            current_user: User performing the update (must have USERS_UPDATE permission)

        Returns:
            Updated user

        Raises:
            NotFoundError: If user not found
            ValidationError: If user doesn't have permission
        """
        # Check if current user has permission to update users
        if not has_permission(
            current_user.role,
            Permission.USERS_UPDATE,
            current_user.custom_permissions,
        ):
            raise ValidationError(
                message="You don't have permission to update user roles",
                details={"user_id": str(user_id)},
            )

        # Get user to verify they exist
        await self.get_user_by_id(user_id)

        # Update fields
        update_dict = role_data.model_dump(exclude_unset=True)
        updated_user = await self.user_repo.update(user_id, update_dict)

        if not updated_user:
            raise NotFoundError(
                message="User not found",
                details={"user_id": str(user_id)},
            )

        logger.info(
            "user_role_updated",
            user_id=str(user_id),
            updated_fields=list(update_dict.keys()),
            updated_by=str(current_user.id),
        )

        return updated_user

    async def approve_or_reject_user(
        self,
        user_id: UUID,
        action: str,
        current_user: User,
    ) -> User:
        """
        Approve or reject a pending Aretan user.

        Args:
            user_id: User ID to approve/reject
            action: "approve" or "reject"
            current_user: Admin performing the action

        Returns:
            Updated user

        Raises:
            NotFoundError: If user not found
            ValidationError: If user is not in pending status or not an aretan
        """
        user = await self.get_user_by_id(user_id)

        if user.role != "aretan":
            raise ValidationError(
                message="Only Aretan users can be approved or rejected",
                details={"user_id": str(user_id), "role": user.role},
            )

        if user.status != "pending":
            raise ValidationError(
                message=f"User is not pending approval (current status: {user.status})",
                details={"user_id": str(user_id), "status": user.status},
            )

        new_status = "active" if action == "approve" else "rejected"
        updated_user = await self.user_repo.update(user_id, {"status": new_status})

        if not updated_user:
            raise NotFoundError(
                message="User not found",
                details={"user_id": str(user_id)},
            )

        logger.info(
            "user_approval_action",
            user_id=str(user_id),
            action=action,
            new_status=new_status,
            performed_by=str(current_user.id),
        )

        # Send email notification (non-blocking)
        try:
            if new_status == "active":
                await email_service.send_approval_approved(updated_user.email, updated_user.first_name)
            else:
                await email_service.send_approval_rejected(updated_user.email, updated_user.first_name)
        except Exception as e:
            logger.warning("email_send_failed", error=str(e), type="approval")

        return updated_user

    async def get_pending_users(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[User], int]:
        """
        Get all users pending approval.

        Args:
            skip: Pagination offset
            limit: Page size

        Returns:
            Tuple of (users list, total count)
        """
        users = await self.user_repo.get_all(
            skip=skip,
            limit=limit,
            filters={"status": "pending"},
        )
        total = await self.user_repo.count(filters={"status": "pending"})
        return users, total

    async def _toggle_user_content(self, user_id: UUID, hidden: bool) -> None:
        """Hide or show all posts and comments by a user."""
        if not self.db:
            return

        await self.db.execute(
            sa_update(Post).where(Post.author_id == user_id).values(is_hidden=hidden)
        )
        await self.db.execute(
            sa_update(Comment).where(Comment.author_id == user_id).values(is_hidden=hidden)
        )
        await self.db.flush()

        action = "hidden" if hidden else "shown"
        logger.info(f"user_content_{action}", user_id=str(user_id))
