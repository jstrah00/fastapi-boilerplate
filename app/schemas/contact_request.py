"""
Contact request schemas for PROF-03.

Contractors can request contact info from aretans.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from app.schemas.post import PostAuthor


class ContactRequestCreate(BaseModel):
    """Schema for creating a contact request."""

    target_id: UUID
    message: str | None = Field(None, max_length=500)


class ContactRequestUpdate(BaseModel):
    """Schema for responding to a contact request."""

    status: str = Field(pattern="^(accepted|rejected)$")


class ContactRequestResponse(BaseModel):
    """Contact request response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    requester: PostAuthor
    target: PostAuthor
    status: str
    message: str | None
    created_at: datetime
    updated_at: datetime


class ContactRequestListResponse(BaseModel):
    """List of contact requests."""

    requests: list[ContactRequestResponse]
    total: int
