"""
Repository for feed posts.
"""
from uuid import UUID

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.postgres.post import Post
from app.repositories.base import BaseRepository
from app.common.logging import get_logger

logger = get_logger(__name__)


class PostRepository(BaseRepository[Post]):
    """Repository for Post model with feed-specific queries."""

    def __init__(self, db: AsyncSession):
        super().__init__(Post, db)

    async def get_feed(
        self, skip: int = 0, limit: int = 20
    ) -> list[Post]:
        """Get visible posts ordered by newest first."""
        result = await self.db.execute(
            select(Post)
            .where(Post.is_hidden.is_(False))
            .order_by(desc(Post.created_at))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_feed(self) -> int:
        """Count visible posts."""
        result = await self.db.execute(
            select(func.count()).select_from(Post).where(Post.is_hidden.is_(False))
        )
        return result.scalar_one()

    async def get_by_author(
        self, author_id: UUID, skip: int = 0, limit: int = 20
    ) -> list[Post]:
        """Get posts by a specific author."""
        result = await self.db.execute(
            select(Post)
            .where(Post.author_id == author_id, Post.is_hidden.is_(False))
            .order_by(desc(Post.created_at))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_author(self, author_id: UUID) -> int:
        """Count visible posts by an author."""
        result = await self.db.execute(
            select(func.count())
            .select_from(Post)
            .where(Post.author_id == author_id, Post.is_hidden.is_(False))
        )
        return result.scalar_one()
