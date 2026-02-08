"""
Notification endpoints for the A2W platform.

Lists and manages in-app notifications for the current user.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import CurrentUser
from app.common.logging import get_logger
from app.schemas.notification import NotificationListResponse
from app.services.notification_service import NotificationService
from app.repositories.notification_repo import NotificationRepository
from app.db.postgres import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

logger = get_logger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


async def get_notification_service(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> NotificationService:
    """Build NotificationService."""
    return NotificationService(NotificationRepository(db))


NotifSvc = Annotated[NotificationService, Depends(get_notification_service)]


@router.get("", response_model=NotificationListResponse, summary="List notifications")
async def list_notifications(
    current_user: CurrentUser,
    notif_service: NotifSvc,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> NotificationListResponse:
    """Get the current user's notifications."""
    return await notif_service.get_notifications(current_user.id, skip, limit)


@router.patch(
    "/{notification_id}/read",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Mark as read",
)
async def mark_notification_read(
    notification_id: UUID,
    current_user: CurrentUser,
    notif_service: NotifSvc,
) -> None:
    """Mark a single notification as read."""
    await notif_service.mark_read(notification_id, current_user.id)


@router.post(
    "/mark-all-read",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Mark all read",
)
async def mark_all_notifications_read(
    current_user: CurrentUser,
    notif_service: NotifSvc,
) -> None:
    """Mark all notifications as read."""
    await notif_service.mark_all_read(current_user.id)
