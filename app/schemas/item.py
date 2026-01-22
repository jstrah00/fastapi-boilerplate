"""
Pydantic schemas for Item API endpoints.

Defines request/response DTOs for item CRUD operations.
Use this as a template for creating schemas for your own resources.

Key components:
    - ItemBase: Common fields shared across schemas
    - ItemCreate: Request schema for creating items
    - ItemUpdate: Request schema for updating items (all fields optional)
    - ItemResponse: Response schema with full item data
    - ItemListResponse: Paginated list response

Dependencies:
    - pydantic: Data validation and serialization

Related files:
    - app/models/postgres/item.py: Item model these schemas map to
    - app/services/item_service.py: Uses these for input validation
    - app/api/v1/items.py: API endpoints using these schemas

Common commands:
    - Test: uv run pytest tests/integration/ -k "item"

Example:
    Creating an item via API::

        # POST /api/v1/items/
        {
            "title": "My Item",
            "description": "Optional description"
        }

    Response::

        {
            "id": "uuid-here",
            "title": "My Item",
            "description": "Optional description",
            "owner_id": "user-uuid",
            "status": "active",
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:30:00Z"
        }

    Partial update::

        # PATCH /api/v1/items/{id}
        {"title": "New Title"}  # Only provided fields are updated
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# =============================================================================
# Base Schemas
# =============================================================================

class ItemBase(BaseModel):
    """Base item schema with common fields."""

    title: str = Field(min_length=1, max_length=255)
    description: str | None = None


# =============================================================================
# Request Schemas
# =============================================================================

class ItemCreate(ItemBase):
    """Schema for creating a new item."""

    pass


class ItemUpdate(BaseModel):
    """
    Schema for updating an item.

    All fields are optional - only provided fields will be updated.
    """

    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None


# =============================================================================
# Response Schemas
# =============================================================================

class ItemResponse(ItemBase):
    """Schema for item response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime


class ItemListResponse(BaseModel):
    """Schema for paginated item list."""

    items: list[ItemResponse]
    total: int
    skip: int
    limit: int
