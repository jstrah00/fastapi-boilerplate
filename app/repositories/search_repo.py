"""
Search repository for A2W directory.

Database queries for searching and filtering Aretan and Contractor users
with JOIN across User, Profile, and Master List tables.
"""
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.postgres.user import User
from app.models.postgres.aretan_profile import AretanProfile
from app.models.postgres.contractor_profile import ContractorProfile
from app.models.postgres.master_tables import (
    MasterIndustry,
    MasterProfession,
    MasterSportAchievement,
)
from app.common.logging import get_logger

logger = get_logger(__name__)


class SearchRepository:
    """Repository for directory search queries."""

    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db

    async def search_aretans(
        self,
        *,
        name: str | None = None,
        industry_id: UUID | None = None,
        profession_id: UUID | None = None,
        max_achievement_id: UUID | None = None,
        employment_status: str | None = None,
        country: str | None = None,
        language: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[dict], int]:
        """Search active Aretan users with filters. Returns (results, total)."""
        base_conditions = [
            User.role == "aretan",
            User.status == "active",
        ]

        if name:
            search_term = f"%{name}%"
            base_conditions.append(
                func.concat(User.first_name, ' ', User.last_name).ilike(search_term)
            )
        if country:
            base_conditions.append(User.country.ilike(f"%{country}%"))
        if industry_id:
            base_conditions.append(AretanProfile.industry_id == industry_id)
        if profession_id:
            base_conditions.append(AretanProfile.profession_id == profession_id)
        if max_achievement_id:
            base_conditions.append(AretanProfile.max_achievement_id == max_achievement_id)
        if employment_status:
            base_conditions.append(AretanProfile.employment_status == employment_status)
        if language:
            base_conditions.append(AretanProfile.languages.contains([language]))

        # Count query
        count_q = (
            select(func.count())
            .select_from(User)
            .join(AretanProfile, User.id == AretanProfile.user_id)
            .where(and_(*base_conditions))
        )
        total = (await self.db.execute(count_q)).scalar() or 0

        # Results query
        query = (
            select(
                User.id,
                User.first_name,
                User.last_name,
                User.avatar_url,
                User.country,
                AretanProfile.employment_status,
                AretanProfile.languages,
                AretanProfile.sport_description,
                AretanProfile.professional_description,
                MasterIndustry.name.label("industry_name"),
                MasterProfession.name.label("profession_name"),
                MasterSportAchievement.name.label("max_achievement_name"),
            )
            .join(AretanProfile, User.id == AretanProfile.user_id)
            .outerjoin(MasterIndustry, AretanProfile.industry_id == MasterIndustry.id)
            .outerjoin(MasterProfession, AretanProfile.profession_id == MasterProfession.id)
            .outerjoin(
                MasterSportAchievement,
                AretanProfile.max_achievement_id == MasterSportAchievement.id,
            )
            .where(and_(*base_conditions))
            .order_by(User.first_name, User.last_name)
            .offset(skip)
            .limit(limit)
        )

        rows = (await self.db.execute(query)).all()
        results = [row._asdict() for row in rows]

        return results, total

    async def search_contractors(
        self,
        *,
        name: str | None = None,
        industry_id: UUID | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[dict], int]:
        """Search active Contractor users with filters. Returns (results, total)."""
        base_conditions = [
            User.role == "contratante",
            User.status == "active",
        ]

        if name:
            search_term = f"%{name}%"
            base_conditions.append(
                func.concat(User.first_name, ' ', User.last_name).ilike(search_term)
            )
        if industry_id:
            base_conditions.append(ContractorProfile.industry_id == industry_id)

        # Count query
        count_q = (
            select(func.count())
            .select_from(User)
            .join(ContractorProfile, User.id == ContractorProfile.user_id)
            .where(and_(*base_conditions))
        )
        total = (await self.db.execute(count_q)).scalar() or 0

        # Results query
        query = (
            select(
                User.id,
                User.first_name,
                User.last_name,
                User.avatar_url,
                User.country,
                ContractorProfile.company_name,
                ContractorProfile.entity_type,
                ContractorProfile.description,
                MasterIndustry.name.label("industry_name"),
            )
            .join(ContractorProfile, User.id == ContractorProfile.user_id)
            .outerjoin(MasterIndustry, ContractorProfile.industry_id == MasterIndustry.id)
            .where(and_(*base_conditions))
            .order_by(User.first_name, User.last_name)
            .offset(skip)
            .limit(limit)
        )

        rows = (await self.db.execute(query)).all()
        results = [row._asdict() for row in rows]

        return results, total
