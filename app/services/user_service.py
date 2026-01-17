"""
User service with business logic.

# =============================================================================
# SERVICE LAYER: Contains business logic for user operations.
# Services use repositories for data access and enforce business rules.
# =============================================================================
"""
from uuid import UUID

from app.repositories.user_repo import UserRepository
from app.models.postgres.user import User
from app.schemas.user import UserCreate, UserUpdate, UserRoleUpdate
from app.core.security import get_password_hash, verify_password
from app.core.logging import get_logger
from app.core.exceptions import (
    NotFoundError,
    AlreadyExistsError,
    ValidationError,
)
from app.core.permissions import Permission, has_permission

logger = get_logger(__name__)


class UserService:
    """
    Service for user business logic.

    # EXAMPLE: Shows service layer pattern with:
    # - Input validation
    # - Business rules enforcement
    # - Repository delegation
    """

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

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
        # Get user
        await self.get_user_by_id(user_id)

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
