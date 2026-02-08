"""
Repository for in-app notifications.
"""
from uuid import UUID

from sqlalchemy import select, func, desc, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.postgres.notification import Notification
from app.repositories.base import BaseRepository
from app.common.logging import get_logger

logger = get_logger(__name__)


class NotificationRepository(BaseRepository[Notification]):
    """Repository for Notification model."""

    def __init__(self, db: AsyncSession):
        super().__init__(Notification, db)

    async def get_for_user(
        self, user_id: UUID, skip: int = 0, limit: int = 20
    ) -> list[Notification]:
        """Get notifications for a user, newest first."""
        result = await self.db.execute(
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(desc(Notification.created_at))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_unread(self, user_id: UUID) -> int:
        """Count unread notifications for a user."""
        result = await self.db.execute(
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
        )
        return result.scalar_one()

    async def mark_as_read(self, notification_id: UUID, user_id: UUID) -> bool:
        """Mark a single notification as read. Returns True if updated."""
        result = await self.db.execute(
            update(Notification)
            .where(Notification.id == notification_id, Notification.user_id == user_id)
            .values(is_read=True)
        )
        return result.rowcount > 0

    async def mark_all_read(self, user_id: UUID) -> int:
        """Mark all notifications as read. Returns count updated."""
        result = await self.db.execute(
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
            .values(is_read=True)
        )
        return result.rowcount
