"""
Search schemas for A2W directory.

Request parameter schemas and response schemas for searching
Aretan and Contractor users with filtering and pagination.
"""
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# Search Result Schemas
# =============================================================================

class AretanSearchResult(BaseModel):
    """Single Aretan result in search listing."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    first_name: str
    last_name: str
    avatar_url: str | None = None
    country: str | None = None
    profession_name: str | None = None
    industry_name: str | None = None
    max_achievement_name: str | None = None
    employment_status: str | None = None
    languages: list[str] | None = None
    sport_description: str | None = None
    professional_description: str | None = None


class ContractorSearchResult(BaseModel):
    """Single Contractor result in search listing."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    first_name: str
    last_name: str
    avatar_url: str | None = None
    country: str | None = None
    industry_name: str | None = None
    company_name: str | None = None
    entity_type: str | None = None
    description: str | None = None


class AretanSearchResponse(BaseModel):
    """Paginated Aretan search results."""

    results: list[AretanSearchResult]
    total: int


class ContractorSearchResponse(BaseModel):
    """Paginated Contractor search results."""

    results: list[ContractorSearchResult]
    total: int
