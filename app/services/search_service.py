"""
Search service for A2W directory.

Business logic for searching Aretan and Contractor users
with filtering and pagination.
"""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

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
        self.repo = SearchRepository(db)

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

        return AretanSearchResponse(
            results=[AretanSearchResult(**r) for r in results],
            total=total,
        )

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
