"""
Item API endpoints.

# =============================================================================
# EXAMPLE: Complete CRUD API for Items.
# Use this as a template for your own resource endpoints.
# =============================================================================
"""
from uuid import UUID

from fastapi import APIRouter, status, HTTPException

from app.api.deps import CurrentUser, ItemSvc
from app.schemas.item import (
    ItemCreate,
    ItemUpdate,
    ItemResponse,
    ItemListResponse,
)
from app.common.logging import get_logger
from app.common.exceptions import NotFoundError, ValidationError

logger = get_logger(__name__)

router = APIRouter(prefix="/items", tags=["items"])


@router.post(
    "/",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create item",
    description="Create a new item. The item will be owned by the current user.",
)
async def create_item(
    item_data: ItemCreate,
    current_user: CurrentUser,
    item_service: ItemSvc,
) -> ItemResponse:
    """Create a new item."""
    item = await item_service.create_item(item_data, current_user)
    return ItemResponse.model_validate(item)


@router.get(
    "/",
    response_model=ItemListResponse,
    summary="List items",
    description="List items. Users see their own items, admins see all items.",
)
async def list_items(
    current_user: CurrentUser,
    item_service: ItemSvc,
    skip: int = 0,
    limit: int = 100,
) -> ItemListResponse:
    """List items with pagination."""
    items, total = await item_service.list_items(current_user, skip, limit)

    return ItemListResponse(
        items=[ItemResponse.model_validate(i) for i in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{item_id}",
    response_model=ItemResponse,
    summary="Get item",
    description="Get a specific item by ID.",
)
async def get_item(
    item_id: UUID,
    current_user: CurrentUser,
    item_service: ItemSvc,
) -> ItemResponse:
    """Get item by ID."""
    try:
        item = await item_service.get_item(item_id, current_user)
        return ItemResponse.model_validate(item)
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


@router.patch(
    "/{item_id}",
    response_model=ItemResponse,
    summary="Update item",
    description="Update an item. Only the owner or admin can update.",
)
async def update_item(
    item_id: UUID,
    update_data: ItemUpdate,
    current_user: CurrentUser,
    item_service: ItemSvc,
) -> ItemResponse:
    """Update item."""
    try:
        item = await item_service.update_item(item_id, update_data, current_user)
        return ItemResponse.model_validate(item)
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


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete item",
    description="Delete an item (soft delete). Only the owner or admin can delete.",
)
async def delete_item(
    item_id: UUID,
    current_user: CurrentUser,
    item_service: ItemSvc,
) -> None:
    """Delete item."""
    try:
        await item_service.delete_item(item_id, current_user)
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
