"""
Pydantic schemas for Item API endpoints.

# =============================================================================
# EXAMPLE: CRUD schemas for the Item model.
# Use this as a template for your own resource schemas.
# =============================================================================
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
