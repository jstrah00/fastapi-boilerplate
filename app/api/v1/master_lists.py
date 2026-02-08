"""
Master lists CRUD endpoints for A2W platform.

Public read access for dropdowns, admin-only write access for management.
Covers industries (rubros), professions, and sport achievements.
"""
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.deps import (
    CurrentUser,
    CurrentAdmin,
    IndustryRepo,
    ProfessionRepo,
    AchievementRepo,
)
from app.schemas.registration import (
    MasterListItemCreate,
    MasterListItemUpdate,
    MasterListItemResponse,
)
from app.models.postgres.master_tables import (
    MasterIndustry,
    MasterProfession,
    MasterSportAchievement,
)

router = APIRouter(prefix="/master-lists", tags=["master-lists"])


# =============================================================================
# Industries (Rubros)
# =============================================================================

@router.get("/industries", response_model=list[MasterListItemResponse])
async def list_industries(repo: IndustryRepo) -> list[MasterListItemResponse]:
    """Get all active industries (public, for registration dropdowns)."""
    items = await repo.get_active()
    return [MasterListItemResponse.model_validate(i) for i in items]


@router.post(
    "/industries",
    response_model=MasterListItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_industry(
    data: MasterListItemCreate,
    repo: IndustryRepo,
    current_user: CurrentAdmin,
) -> MasterListItemResponse:
    """Create a new industry (admin only)."""
    existing = await repo.get_by_name(data.name)
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Industry already exists")
    item = MasterIndustry(name=data.name, display_order=data.display_order)
    created = await repo.create(item)
    return MasterListItemResponse.model_validate(created)


@router.patch("/industries/{item_id}", response_model=MasterListItemResponse)
async def update_industry(
    item_id: UUID,
    data: MasterListItemUpdate,
    repo: IndustryRepo,
    current_user: CurrentAdmin,
) -> MasterListItemResponse:
    """Update an industry (admin only)."""
    update_data = data.model_dump(exclude_unset=True)
    updated = await repo.update(item_id, update_data)
    if not updated:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Industry not found")
    return MasterListItemResponse.model_validate(updated)


# =============================================================================
# Professions
# =============================================================================

@router.get("/professions", response_model=list[MasterListItemResponse])
async def list_professions(repo: ProfessionRepo) -> list[MasterListItemResponse]:
    """Get all active professions (public, for registration dropdowns)."""
    items = await repo.get_active()
    return [MasterListItemResponse.model_validate(i) for i in items]


@router.post(
    "/professions",
    response_model=MasterListItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_profession(
    data: MasterListItemCreate,
    repo: ProfessionRepo,
    current_user: CurrentAdmin,
) -> MasterListItemResponse:
    """Create a new profession (admin only)."""
    existing = await repo.get_by_name(data.name)
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Profession already exists")
    item = MasterProfession(name=data.name, display_order=data.display_order)
    created = await repo.create(item)
    return MasterListItemResponse.model_validate(created)


@router.patch("/professions/{item_id}", response_model=MasterListItemResponse)
async def update_profession(
    item_id: UUID,
    data: MasterListItemUpdate,
    repo: ProfessionRepo,
    current_user: CurrentAdmin,
) -> MasterListItemResponse:
    """Update a profession (admin only)."""
    update_data = data.model_dump(exclude_unset=True)
    updated = await repo.update(item_id, update_data)
    if not updated:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Profession not found")
    return MasterListItemResponse.model_validate(updated)


# =============================================================================
# Sport Achievements
# =============================================================================

@router.get("/sport-achievements", response_model=list[MasterListItemResponse])
async def list_sport_achievements(
    repo: AchievementRepo,
) -> list[MasterListItemResponse]:
    """Get all active sport achievement levels (public, for registration dropdowns)."""
    items = await repo.get_active()
    return [MasterListItemResponse.model_validate(i) for i in items]


@router.post(
    "/sport-achievements",
    response_model=MasterListItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_sport_achievement(
    data: MasterListItemCreate,
    repo: AchievementRepo,
    current_user: CurrentAdmin,
) -> MasterListItemResponse:
    """Create a new sport achievement level (admin only)."""
    existing = await repo.get_by_name(data.name)
    if existing:
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="Sport achievement already exists"
        )
    item = MasterSportAchievement(name=data.name, display_order=data.display_order)
    created = await repo.create(item)
    return MasterListItemResponse.model_validate(created)


@router.patch(
    "/sport-achievements/{item_id}", response_model=MasterListItemResponse
)
async def update_sport_achievement(
    item_id: UUID,
    data: MasterListItemUpdate,
    repo: AchievementRepo,
    current_user: CurrentAdmin,
) -> MasterListItemResponse:
    """Update a sport achievement level (admin only)."""
    update_data = data.model_dump(exclude_unset=True)
    updated = await repo.update(item_id, update_data)
    if not updated:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="Sport achievement not found"
        )
    return MasterListItemResponse.model_validate(updated)
