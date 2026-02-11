"""
Search service for A2W directory.

Business logic for searching Aretan and Contractor users
with filtering and pagination.
"""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.postgres.master_tables import MasterIndustry, MasterProfession
from app.repositories.search_repo import SearchRepository
from app.schemas.search import (
    AretanSearchResult,
    AretanSearchResponse,
    ContractorSearchResult,
    ContractorSearchResponse,
)
from app.common.logging import get_logger

logger = get_logger(__name__)


class SearchService:
    """Service for directory search business logic."""

    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db
        self.repo = SearchRepository(db)

    async def _resolve_names(
        self, industry_ids: set[UUID], profession_ids: set[UUID]
    ) -> tuple[dict[UUID, str], dict[UUID, str]]:
        """Bulk-resolve industry and profession IDs to names."""
        ind_map: dict[UUID, str] = {}
        prof_map: dict[UUID, str] = {}

        if industry_ids:
            rows = (await self.db.execute(
                select(MasterIndustry.id, MasterIndustry.name)
                .where(MasterIndustry.id.in_(industry_ids))
            )).all()
            ind_map = {r.id: r.name for r in rows}

        if profession_ids:
            rows = (await self.db.execute(
                select(MasterProfession.id, MasterProfession.name)
                .where(MasterProfession.id.in_(profession_ids))
            )).all()
            prof_map = {r.id: r.name for r in rows}

        return ind_map, prof_map

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
    ) -> AretanSearchResponse:
        """Search Aretan users with filters."""
        results, total = await self.repo.search_aretans(
            name=name,
            industry_id=industry_id,
            profession_id=profession_id,
            max_achievement_id=max_achievement_id,
            employment_status=employment_status,
            country=country,
            language=language,
            skip=skip,
            limit=limit,
        )

        # Collect all IDs for bulk resolution
        all_ind_ids: set[UUID] = set()
        all_prof_ids: set[UUID] = set()
        for r in results:
            if r.get("industry_ids"):
                all_ind_ids.update(r["industry_ids"])
            if r.get("profession_ids"):
                all_prof_ids.update(r["profession_ids"])

        ind_map, prof_map = await self._resolve_names(all_ind_ids, all_prof_ids)

        search_results = []
        for r in results:
            ind_names = [ind_map[uid] for uid in (r.pop("industry_ids", None) or []) if uid in ind_map]
            prof_names = [prof_map[uid] for uid in (r.pop("profession_ids", None) or []) if uid in prof_map]
            search_results.append(
                AretanSearchResult(**r, industry_names=ind_names, profession_names=prof_names)
            )

        return AretanSearchResponse(results=search_results, total=total)

    async def search_contractors(
        self,
        *,
        name: str | None = None,
        industry_id: UUID | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> ContractorSearchResponse:
        """Search Contractor users with filters."""
        results, total = await self.repo.search_contractors(
            name=name,
            industry_id=industry_id,
            skip=skip,
            limit=limit,
        )

        return ContractorSearchResponse(
            results=[ContractorSearchResult(**r) for r in results],
            total=total,
        )
