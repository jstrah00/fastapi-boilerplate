"""
Directory search endpoints for A2W platform.

Search and filter Aretan and Contractor users with pagination.
Protected by directory permissions.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.api.deps import CurrentUser
from app.common.permissions import Permission, require_permissions
from app.db.postgres import get_db
from app.services.search_service import SearchService
from app.schemas.search import AretanSearchResponse, ContractorSearchResponse
from app.common.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/search", tags=["directory"])


async def get_search_service(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> SearchService:
    """Get search service instance."""
    return SearchService(db)


SearchSvc = Annotated[SearchService, Depends(get_search_service)]


@router.get(
    "/aretans",
    response_model=AretanSearchResponse,
    summary="Search Aretan users",
)
async def search_aretans(
    search_service: SearchSvc,
    current_user: Annotated[
        CurrentUser, Depends(require_permissions(Permission.DIRECTORY_ARETANS))
    ],
    name: str | None = Query(None, description="Search by name"),
    industry_id: UUID | None = Query(None, description="Filter by industry"),
    profession_id: UUID | None = Query(None, description="Filter by profession"),
    max_achievement_id: UUID | None = Query(None, description="Filter by max achievement"),
    employment_status: str | None = Query(None, description="Filter by employment status"),
    country: str | None = Query(None, description="Filter by country"),
    language: str | None = Query(None, description="Filter by language"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> AretanSearchResponse:
    """Search active Aretan users with optional filters."""
    return await search_service.search_aretans(
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


@router.get(
    "/contractors",
    response_model=ContractorSearchResponse,
    summary="Search Contractor users",
)
async def search_contractors(
    search_service: SearchSvc,
    current_user: Annotated[
        CurrentUser, Depends(require_permissions(Permission.DIRECTORY_CONTRACTORS))
    ],
    name: str | None = Query(None, description="Search by name"),
    industry_id: UUID | None = Query(None, description="Filter by industry"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> ContractorSearchResponse:
    """Search active Contractor users with optional filters."""
    return await search_service.search_contractors(
        name=name,
        industry_id=industry_id,
        skip=skip,
        limit=limit,
    )
