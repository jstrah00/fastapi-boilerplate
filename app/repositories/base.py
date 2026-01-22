"""
Base repository with common CRUD operations.

Provides a generic repository pattern implementation that abstracts data access
operations from business logic, with support for pagination and filtering.

Key components:
    - BaseRepository[T]: Generic repository class for SQLAlchemy models
    - get: Retrieve single record by ID
    - get_all: Retrieve multiple records with pagination and filters
    - count: Count records matching filters
    - create: Insert new record
    - update: Update existing record by ID
    - delete: Hard delete record by ID
    - soft_delete: Soft delete by setting status to 'inactive'

Dependencies:
    - sqlalchemy: ORM operations
    - app.common.logging: Structured logging

Related files:
    - app/repositories/user_repo.py: User-specific repository
    - app/repositories/item_repo.py: Item-specific repository
    - app/services/: Services that use repositories

Common commands:
    - Test: uv run pytest tests/ -k "repository"

Example:
    Creating a custom repository::

        from app.repositories.base import BaseRepository
        from app.models.postgres.product import Product

        class ProductRepository(BaseRepository[Product]):
            def __init__(self, db: AsyncSession):
                super().__init__(Product, db)

            async def get_by_category(self, category_id: UUID) -> list[Product]:
                result = await self.db.execute(
                    select(Product).where(Product.category_id == category_id)
                )
                return list(result.scalars().all())

    Using the base repository::

        repo = UserRepository(db)
        user = await repo.get(user_id)
        users = await repo.get_all(skip=0, limit=10, filters={"status": "active"})
        total = await repo.count(filters={"role": "admin"})
"""
from typing import Generic, TypeVar, Type, Any
from uuid import UUID

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.logging import get_logger

T = TypeVar("T")

logger = get_logger(__name__)


class BaseRepository(Generic[T]):
    """
    Base repository with common CRUD operations.

    Type parameter T should be a SQLAlchemy model.

    # EXAMPLE USAGE:
    # class UserRepository(BaseRepository[User]):
    #     def __init__(self, db: AsyncSession):
    #         super().__init__(User, db)
    #
    #     async def get_by_email(self, email: str) -> User | None:
    #         # Custom query method
    #         ...
    """

    def __init__(self, model: Type[T], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id: UUID) -> T | None:
        """
        Get a single record by ID.

        Args:
            id: Record ID

        Returns:
            Record if found, None otherwise
        """
        result = await self.db.execute(select(self.model).where(self.model.id == id))
        record = result.scalar_one_or_none()

        if record:
            logger.debug(
                "repository_get_success",
                model=self.model.__name__,
                id=str(id),
            )
        else:
            logger.debug(
                "repository_get_not_found",
                model=self.model.__name__,
                id=str(id),
            )

        return record

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: dict[str, Any] | None = None,
    ) -> list[T]:
        """
        Get all records with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Optional filters as {column_name: value}

        Returns:
            List of records
        """
        query = select(self.model)

        # Apply filters
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)

        # Apply pagination
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        records = list(result.scalars().all())

        logger.debug(
            "repository_get_all",
            model=self.model.__name__,
            count=len(records),
            skip=skip,
            limit=limit,
        )

        return records

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        """
        Count records matching filters.

        Args:
            filters: Optional filters as {column_name: value}

        Returns:
            Number of matching records
        """
        query = select(func.count()).select_from(self.model)

        # Apply filters
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)

        result = await self.db.execute(query)
        count = result.scalar_one()

        logger.debug(
            "repository_count",
            model=self.model.__name__,
            count=count,
            filters=filters,
        )

        return count

    async def create(self, obj: T) -> T:
        """
        Create a new record.

        Args:
            obj: Object to create

        Returns:
            Created object
        """
        self.db.add(obj)
        await self.db.flush()
        await self.db.refresh(obj)

        logger.info(
            "repository_create_success",
            model=self.model.__name__,
            id=str(obj.id) if hasattr(obj, "id") else None,
        )

        return obj

    async def update(self, id: UUID, data: dict[str, Any]) -> T | None:
        """
        Update a record.

        Args:
            id: Record ID
            data: Fields to update

        Returns:
            Updated record if found, None otherwise
        """
        # Check if record exists
        record = await self.get(id)
        if not record:
            logger.warning(
                "repository_update_not_found",
                model=self.model.__name__,
                id=str(id),
            )
            return None

        # Update fields
        for key, value in data.items():
            if hasattr(record, key):
                setattr(record, key, value)

        await self.db.flush()
        await self.db.refresh(record)

        logger.info(
            "repository_update_success",
            model=self.model.__name__,
            id=str(id),
            fields=list(data.keys()),
        )

        return record

    async def delete(self, id: UUID) -> bool:
        """
        Delete a record (hard delete).

        Args:
            id: Record ID

        Returns:
            True if deleted, False if not found
        """
        result = await self.db.execute(
            delete(self.model).where(self.model.id == id)
        )

        deleted = result.rowcount > 0

        if deleted:
            logger.info(
                "repository_delete_success",
                model=self.model.__name__,
                id=str(id),
            )
        else:
            logger.warning(
                "repository_delete_not_found",
                model=self.model.__name__,
                id=str(id),
            )

        return deleted

    async def soft_delete(self, id: UUID) -> T | None:
        """
        Soft delete a record by setting status to 'inactive'.

        Args:
            id: Record ID

        Returns:
            Updated record if found, None otherwise
        """
        if not hasattr(self.model, "status"):
            raise AttributeError(f"{self.model.__name__} does not have a 'status' field")

        return await self.update(id, {"status": "inactive"})
