"""
Item repository for data access operations.

# =============================================================================
# EXAMPLE REPOSITORY: Shows a simple CRUD repository for Items.
# Use this as a template for your own repositories.
# =============================================================================
"""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.postgres.item import Item
from app.repositories.base import BaseRepository
from app.common.logging import get_logger

logger = get_logger(__name__)


class ItemRepository(BaseRepository[Item]):
    """
    Repository for Item model.

    # EXAMPLE: Simple CRUD repository with owner-based filtering.
    """

    def __init__(self, db: AsyncSession):
        super().__init__(Item, db)

    async def get_by_owner(
        self,
        owner_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Item]:
        """
        Get all items owned by a specific user.

        Args:
            owner_id: Owner user ID
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of items owned by the user
        """
        result = await self.db.execute(
            select(Item)
            .where(Item.owner_id == owner_id)
            .where(Item.status == "active")
            .offset(skip)
            .limit(limit)
        )
        items = list(result.scalars().all())

        logger.debug(
            "item_get_by_owner",
            owner_id=str(owner_id),
            count=len(items),
        )

        return items

    async def count_by_owner(self, owner_id: UUID) -> int:
        """
        Count items owned by a specific user.

        Args:
            owner_id: Owner user ID

        Returns:
            Number of items
        """
        return await self.count(filters={"owner_id": owner_id, "status": "active"})
