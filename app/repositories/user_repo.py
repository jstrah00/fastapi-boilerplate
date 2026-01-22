"""
User repository for data access operations.

Extends BaseRepository with user-specific queries for authentication,
filtering, and user management operations.

Key components:
    - UserRepository: Repository for User model
    - get_by_email: Find user by email address
    - get_active_users: Get paginated list of active users
    - get_admins: Get all admin users

Dependencies:
    - sqlalchemy: ORM operations
    - app.repositories.base: BaseRepository class
    - app.models.postgres.user: User model

Related files:
    - app/models/postgres/user.py: User model definition
    - app/services/user_service.py: Business logic using this repo
    - app/services/auth_service.py: Auth logic using this repo
    - app/api/deps.py: Dependency injection for this repo

Common commands:
    - Test: uv run pytest tests/ -k "user"

Example:
    Using UserRepository::

        from app.repositories.user_repo import UserRepository

        repo = UserRepository(db)

        # Find by email (for login)
        user = await repo.get_by_email("user@example.com")

        # Get paginated active users
        users = await repo.get_active_users(skip=0, limit=20)

        # Get all admins
        admins = await repo.get_admins()

        # Inherited from BaseRepository
        user = await repo.get(user_id)
        await repo.create(new_user)
        await repo.update(user_id, {"status": "inactive"})
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.postgres.user import User
from app.repositories.base import BaseRepository
from app.common.logging import get_logger

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
