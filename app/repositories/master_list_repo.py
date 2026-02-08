"""
Repository for master list tables (industries, professions, sport achievements).

Provides CRUD operations for admin-managed lookup tables.
"""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from app.models.postgres.master_tables import (
    MasterIndustry,
    MasterProfession,
    MasterSportAchievement,
)
from app.common.logging import get_logger

logger = get_logger(__name__)


class MasterIndustryRepository(BaseRepository[MasterIndustry]):
    """Repository for industries (rubros)."""

    def __init__(self, db: AsyncSession):
        super().__init__(MasterIndustry, db)

    async def get_by_name(self, name: str) -> MasterIndustry | None:
        """Get industry by name."""
        result = await self.db.execute(
            select(MasterIndustry).where(MasterIndustry.name == name)
        )
        return result.scalar_one_or_none()

    async def get_active(self) -> list[MasterIndustry]:
        """Get all active industries ordered by display_order."""
        result = await self.db.execute(
            select(MasterIndustry)
            .where(MasterIndustry.is_active.is_(True))
            .order_by(MasterIndustry.display_order, MasterIndustry.name)
        )
        return list(result.scalars().all())


class MasterProfessionRepository(BaseRepository[MasterProfession]):
    """Repository for professions."""

    def __init__(self, db: AsyncSession):
        super().__init__(MasterProfession, db)

    async def get_by_name(self, name: str) -> MasterProfession | None:
        """Get profession by name."""
        result = await self.db.execute(
            select(MasterProfession).where(MasterProfession.name == name)
        )
        return result.scalar_one_or_none()

    async def get_active(self) -> list[MasterProfession]:
        """Get all active professions ordered by display_order."""
        result = await self.db.execute(
            select(MasterProfession)
            .where(MasterProfession.is_active.is_(True))
            .order_by(MasterProfession.display_order, MasterProfession.name)
        )
        return list(result.scalars().all())


class MasterSportAchievementRepository(BaseRepository[MasterSportAchievement]):
    """Repository for sport achievement levels."""

    def __init__(self, db: AsyncSession):
        super().__init__(MasterSportAchievement, db)

    async def get_by_name(self, name: str) -> MasterSportAchievement | None:
        """Get sport achievement by name."""
        result = await self.db.execute(
            select(MasterSportAchievement).where(
                MasterSportAchievement.name == name
            )
        )
        return result.scalar_one_or_none()

    async def get_active(self) -> list[MasterSportAchievement]:
        """Get all active achievements ordered by display_order."""
        result = await self.db.execute(
            select(MasterSportAchievement)
            .where(MasterSportAchievement.is_active.is_(True))
            .order_by(MasterSportAchievement.display_order)
        )
        return list(result.scalars().all())
