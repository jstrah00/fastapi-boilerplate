"""
Repository for post likes.
"""
from uuid import UUID

from sqlalchemy import select, func, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.postgres.post_like import PostLike
from app.repositories.base import BaseRepository
from app.common.logging import get_logger

logger = get_logger(__name__)


class PostLikeRepository(BaseRepository[PostLike]):
    """Repository for PostLike model."""

    def __init__(self, db: AsyncSession):
        super().__init__(PostLike, db)

    async def get_by_post_and_user(
        self, post_id: UUID, user_id: UUID
    ) -> PostLike | None:
        """Check if a user liked a specific post."""
        result = await self.db.execute(
            select(PostLike).where(
                PostLike.post_id == post_id, PostLike.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def delete_by_post_and_user(
        self, post_id: UUID, user_id: UUID
    ) -> bool:
        """Remove a like. Returns True if deleted."""
        result = await self.db.execute(
            sa_delete(PostLike).where(
                PostLike.post_id == post_id, PostLike.user_id == user_id
            )
        )
        return result.rowcount > 0

    async def get_likers(
        self, post_id: UUID, skip: int = 0, limit: int = 50
    ) -> list[PostLike]:
        """Get likes for a post (with user relationship loaded)."""
        result = await self.db.execute(
            select(PostLike)
            .where(PostLike.post_id == post_id)
            .order_by(PostLike.created_at)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_liked_post_ids(
        self, user_id: UUID, post_ids: list[UUID]
    ) -> set[UUID]:
        """Get which posts from a list the user has liked."""
        if not post_ids:
            return set()
        result = await self.db.execute(
            select(PostLike.post_id).where(
                PostLike.user_id == user_id,
                PostLike.post_id.in_(post_ids),
            )
        )
        return {row[0] for row in result.all()}
