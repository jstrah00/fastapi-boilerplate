"""
User repository for data access operations.

# =============================================================================
# EXAMPLE REPOSITORY: Extends BaseRepository with user-specific queries.
# =============================================================================
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.postgres.user import User
from app.repositories.base import BaseRepository
from app.core.logging import get_logger

logger = get_logger(__name__)


class UserRepository(BaseRepository[User]):
    """
    Repository for User model with specific query methods.

    # EXAMPLE: This shows how to extend BaseRepository
    # with domain-specific queries.
    """

    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> User | None:
        """
        Get user by email.

        Args:
            email: User email

        Returns:
            User if found, None otherwise
        """
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        logger.debug(
            "user_get_by_email",
            email=email,
            found=user is not None,
        )

        return user

    async def get_active_users(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[User]:
        """
        Get all active users.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of active users
        """
        return await self.get_all(
            skip=skip,
            limit=limit,
            filters={"status": "active"},
        )

    async def get_admins(self) -> list[User]:
        """
        Get all admin users.

        Returns:
            List of admin users
        """
        result = await self.db.execute(
            select(User).where(User.is_admin == True)  # noqa: E712
        )
        users = list(result.scalars().all())

        logger.debug(
            "user_get_admins",
            count=len(users),
        )

        return users
