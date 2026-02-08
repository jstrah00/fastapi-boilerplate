"""
Repository for post comments.
"""
from uuid import UUID

from sqlalchemy import select, func, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.postgres.comment import Comment
from app.repositories.base import BaseRepository
from app.common.logging import get_logger

logger = get_logger(__name__)


class CommentRepository(BaseRepository[Comment]):
    """Repository for Comment model."""

    def __init__(self, db: AsyncSession):
        super().__init__(Comment, db)

    async def get_by_post(
        self, post_id: UUID, skip: int = 0, limit: int = 50
    ) -> list[Comment]:
        """Get visible comments for a post, oldest first."""
        result = await self.db.execute(
            select(Comment)
            .where(Comment.post_id == post_id, Comment.is_hidden.is_(False))
            .order_by(asc(Comment.created_at))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_post(self, post_id: UUID) -> int:
        """Count visible comments on a post."""
        result = await self.db.execute(
            select(func.count())
            .select_from(Comment)
            .where(Comment.post_id == post_id, Comment.is_hidden.is_(False))
        )
        return result.scalar_one()
