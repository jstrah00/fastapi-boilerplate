"""
Schemas for in-app notifications.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.post import PostAuthor


class NotificationResponse(BaseModel):
    """Single notification item."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: str
    actor: PostAuthor
    post_id: UUID | None = None
    extra_data: dict | None = None
    is_read: bool
    created_at: datetime


class NotificationListResponse(BaseModel):
    """Paginated list of notifications with unread count."""

    notifications: list[NotificationResponse]
    unread_count: int
