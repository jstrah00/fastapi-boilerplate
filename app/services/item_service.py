"""
Item service with business logic.

Contains CRUD business logic for items with ownership-based authorization.
Use this as a template for creating services for your own resources.

Key components:
    - ItemService: Service class for item operations
    - get_item: Get item with ownership/admin check
    - list_items: List items (own for users, all for admins)
    - create_item: Create item owned by current user
    - update_item: Update item (owner or admin only)
    - delete_item: Soft delete item (owner or admin only)

Dependencies:
    - app.repositories.item_repo: Item data access
    - app.common.exceptions: Business error types

Related files:
    - app/api/v1/items.py: Item API endpoints
    - app/repositories/item_repo.py: Data access layer
    - app/schemas/item.py: Request/response schemas

Common commands:
    - Test: uv run pytest tests/ -k "item"

Example:
    Creating an item::

        item_service = ItemService(item_repo)

        item = await item_service.create_item(
            data=ItemCreate(title="My Item", description="Description"),
            owner=current_user
        )

    Listing items::

        items, total = await item_service.list_items(
            current_user=user,
            skip=0,
            limit=20
        )
        # Regular users see their own items
        # Admins see all items

    Updating with authorization::

        updated = await item_service.update_item(
            item_id=item_id,
            data=ItemUpdate(title="New Title"),
            current_user=user  # Must be owner or admin
        )
        # Raises ValidationError if not authorized
        # Raises NotFoundError if item doesn't exist
"""
from uuid import UUID

from app.repositories.item_repo import ItemRepository
from app.models.postgres.item import Item
from app.models.postgres.user import User
from app.schemas.item import ItemCreate, ItemUpdate
from app.common.logging import get_logger
from app.common.exceptions import NotFoundError, ValidationError

logger = get_logger(__name__)


class ItemService:
    """
    Service for item business logic.

    # EXAMPLE: Shows CRUD operations with ownership checks.
    """

    def __init__(self, item_repo: ItemRepository):
        self.item_repo = item_repo

    async def get_item(self, item_id: UUID, current_user: User) -> Item:
        """
        Get item by ID.

        Args:
            item_id: Item ID
            current_user: User requesting the item

        Returns:
            Item object

        Raises:
            NotFoundError: If item not found
            ValidationError: If user doesn't have access
        """
        item = await self.item_repo.get(item_id)
        if not item or item.status != "active":
            raise NotFoundError(
                message="Item not found",
                details={"item_id": str(item_id)},
            )

        # Check ownership (admin can see any item)
        if item.owner_id != current_user.id and not current_user.is_admin:
            raise ValidationError(
                message="You don't have access to this item",
                details={"item_id": str(item_id)},
            )

        return item

    async def list_items(
        self,
        current_user: User,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Item], int]:
        """
        List items for current user.

        Args:
            current_user: User requesting items
            skip: Pagination offset
            limit: Maximum items to return

        Returns:
            Tuple of (items list, total count)
        """
        # Admin sees all items, regular users see only their own
        if current_user.is_admin:
            items = await self.item_repo.get_all(
                skip=skip,
                limit=limit,
                filters={"status": "active"},
            )
            total = await self.item_repo.count(filters={"status": "active"})
        else:
            items = await self.item_repo.get_by_owner(
                owner_id=current_user.id,
                skip=skip,
                limit=limit,
            )
            total = await self.item_repo.count_by_owner(current_user.id)

        return items, total

    async def create_item(self, item_data: ItemCreate, owner: User) -> Item:
        """
        Create a new item.

        Args:
            item_data: Item creation data
            owner: User creating the item

        Returns:
            Created item
        """
        item = Item(
            title=item_data.title,
            description=item_data.description,
            owner_id=owner.id,
            status="active",
        )

        created_item = await self.item_repo.create(item)

        logger.info(
            "item_created",
            item_id=str(created_item.id),
            owner_id=str(owner.id),
        )

        return created_item

    async def update_item(
        self,
        item_id: UUID,
        update_data: ItemUpdate,
        current_user: User,
    ) -> Item:
        """
        Update an item.

        Args:
            item_id: Item ID
            update_data: Update data
            current_user: User performing the update

        Returns:
            Updated item

        Raises:
            NotFoundError: If item not found
            ValidationError: If user doesn't have permission
        """
        # Get item (also checks ownership)
        item = await self.get_item(item_id, current_user)

        # Only owner can update (or admin)
        if item.owner_id != current_user.id and not current_user.is_admin:
            raise ValidationError(
                message="You don't have permission to update this item",
                details={"item_id": str(item_id)},
            )

        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        updated_item = await self.item_repo.update(item_id, update_dict)

        if not updated_item:
            raise NotFoundError(
                message="Item not found",
                details={"item_id": str(item_id)},
            )

        logger.info(
            "item_updated",
            item_id=str(item_id),
            updated_by=str(current_user.id),
        )

        return updated_item

    async def delete_item(self, item_id: UUID, current_user: User) -> None:
        """
        Delete an item (soft delete).

        Args:
            item_id: Item ID
            current_user: User performing the deletion

        Raises:
            NotFoundError: If item not found
            ValidationError: If user doesn't have permission
        """
        # Get item (also checks ownership)
        item = await self.get_item(item_id, current_user)

        # Only owner can delete (or admin)
        if item.owner_id != current_user.id and not current_user.is_admin:
            raise ValidationError(
                message="You don't have permission to delete this item",
                details={"item_id": str(item_id)},
            )

        # Soft delete
        await self.item_repo.soft_delete(item_id)

        logger.info(
            "item_deleted",
            item_id=str(item_id),
            deleted_by=str(current_user.id),
        )
