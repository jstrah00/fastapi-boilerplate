"""
Contact request repository.
"""
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.postgres.contact_request import ContactRequest
from app.repositories.base import BaseRepository
from app.common.logging import get_logger

logger = get_logger(__name__)


class ContactRequestRepository(BaseRepository[ContactRequest]):
    """Repository for contact requests."""

    def __init__(self, db: AsyncSession):
        super().__init__(ContactRequest, db)

    async def get_by_users(
        self, requester_id: UUID, target_id: UUID
    ) -> ContactRequest | None:
        """Get request between two specific users."""
        result = await self.db.execute(
            select(ContactRequest).where(
                and_(
                    ContactRequest.requester_id == requester_id,
                    ContactRequest.target_id == target_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_received_requests(
        self, user_id: UUID, skip: int = 0, limit: int = 20
    ) -> list[ContactRequest]:
        """Get requests received by a user (where user is target)."""
        result = await self.db.execute(
            select(ContactRequest)
            .where(ContactRequest.target_id == user_id)
            .order_by(ContactRequest.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_received(self, user_id: UUID) -> int:
        """Count received requests."""
        from sqlalchemy import func

        result = await self.db.execute(
            select(func.count())
            .select_from(ContactRequest)
            .where(ContactRequest.target_id == user_id)
        )
        return result.scalar() or 0
