"""
Notification service for creating and managing in-app notifications.
"""
from uuid import UUID

from app.models.postgres.notification import Notification
from app.repositories.notification_repo import NotificationRepository
from app.schemas.notification import NotificationListResponse, NotificationResponse
from app.schemas.post import PostAuthor
from app.common.logging import get_logger

logger = get_logger(__name__)


class NotificationService:
    """Service for notification business logic."""

    def __init__(self, notification_repo: NotificationRepository):
        self.notification_repo = notification_repo

    async def get_notifications(
        self, user_id: UUID, skip: int = 0, limit: int = 20
    ) -> NotificationListResponse:
        """Get paginated notifications with unread count."""
        notifications = await self.notification_repo.get_for_user(user_id, skip, limit)
        unread_count = await self.notification_repo.count_unread(user_id)

        return NotificationListResponse(
            notifications=[
                NotificationResponse(
                    id=n.id,
                    type=n.type,
                    actor=PostAuthor(
                        id=n.actor.id,
                        first_name=n.actor.first_name,
                        last_name=n.actor.last_name,
                        avatar_url=n.actor.avatar_url,
                        role=n.actor.role,
                    ),
                    post_id=n.post_id,
                    is_read=n.is_read,
                    created_at=n.created_at,
                )
                for n in notifications
            ],
            unread_count=unread_count,
        )

    async def mark_read(self, notification_id: UUID, user_id: UUID) -> None:
        """Mark a notification as read."""
        await self.notification_repo.mark_as_read(notification_id, user_id)

    async def mark_all_read(self, user_id: UUID) -> None:
        """Mark all notifications as read."""
        await self.notification_repo.mark_all_read(user_id)

    async def create_notification(
        self,
        user_id: UUID,
        actor_id: UUID,
        notification_type: str,
        post_id: UUID | None = None,
        comment_id: UUID | None = None,
    ) -> None:
        """Create a notification. Skips if user == actor (no self-notifications)."""
        if user_id == actor_id:
            return

        notification = Notification(
            user_id=user_id,
            actor_id=actor_id,
            type=notification_type,
            post_id=post_id,
            comment_id=comment_id,
        )
        await self.notification_repo.create(notification)
        logger.info(
            "notification_created",
            type=notification_type,
            recipient=str(user_id),
            actor=str(actor_id),
        )
