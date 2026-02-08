"""
Profile endpoints for A2W platform.

Public profile views and own-profile editing for Aretan and Contratante users,
including work experience CRUD for Aretans.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import CurrentUser, get_current_user
from app.services.profile_service import ProfileService
from app.schemas.profile import (
    AretanPublicProfile,
    ContractorPublicProfile,
    AretanProfileResponse,
    AretanProfileUpdate,
    ContractorProfileResponse,
    ContractorProfileUpdate,
    WorkExperienceResponse,
    WorkExperienceCreate,
    WorkExperienceUpdate,
)
from app.schemas.user import UserResponse
from app.common.exceptions import NotFoundError, ValidationError
from app.common.logging import get_logger
from app.db.postgres import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from fastapi import Depends as FastAPIDepends

logger = get_logger(__name__)

router = APIRouter(prefix="/profiles", tags=["profiles"])


async def get_profile_service(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> ProfileService:
    """Get profile service instance."""
    return ProfileService(db)


ProfileSvc = Annotated[ProfileService, Depends(get_profile_service)]


# =============================================================================
# Public Profile Views
# =============================================================================

@router.get(
    "/aretan/{user_id}",
    response_model=AretanPublicProfile,
    summary="Get Aretan public profile",
)
async def get_aretan_profile(
    user_id: UUID,
    profile_service: ProfileSvc,
    current_user: CurrentUser,
) -> AretanPublicProfile:
    """View an Aretan user's public profile."""
    try:
        return await profile_service.get_aretan_profile(user_id, viewer=current_user)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.get(
    "/contractor/{user_id}",
    response_model=ContractorPublicProfile,
    summary="Get Contractor public profile",
)
async def get_contractor_profile(
    user_id: UUID,
    profile_service: ProfileSvc,
    current_user: CurrentUser,
) -> ContractorPublicProfile:
    """View a Contractor user's public profile."""
    try:
        return await profile_service.get_contractor_profile(user_id, viewer=current_user)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


# =============================================================================
# Own Profile - Aretan
# =============================================================================

@router.get(
    "/me/aretan",
    response_model=AretanProfileResponse,
    summary="Get own Aretan profile",
)
async def get_own_aretan_profile(
    current_user: CurrentUser,
) -> AretanProfileResponse:
    """Get the current user's Aretan profile data."""
    if not current_user.aretan_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You don't have an Aretan profile",
        )
    return AretanProfileResponse.model_validate(current_user.aretan_profile)


@router.patch(
    "/me/aretan",
    response_model=AretanProfileResponse,
    summary="Update own Aretan profile",
)
async def update_own_aretan_profile(
    data: AretanProfileUpdate,
    current_user: CurrentUser,
    profile_service: ProfileSvc,
) -> AretanProfileResponse:
    """Update the current user's Aretan profile."""
    try:
        profile = await profile_service.update_aretan_profile(current_user, data)
        return AretanProfileResponse.model_validate(profile)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


# =============================================================================
# Own Profile - Contractor
# =============================================================================

@router.get(
    "/me/contractor",
    response_model=ContractorProfileResponse,
    summary="Get own Contractor profile",
)
async def get_own_contractor_profile(
    current_user: CurrentUser,
) -> ContractorProfileResponse:
    """Get the current user's Contractor profile data."""
    if not current_user.contractor_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You don't have a Contractor profile",
        )
    return ContractorProfileResponse.model_validate(current_user.contractor_profile)


@router.patch(
    "/me/contractor",
    response_model=ContractorProfileResponse,
    summary="Update own Contractor profile",
)
async def update_own_contractor_profile(
    data: ContractorProfileUpdate,
    current_user: CurrentUser,
    profile_service: ProfileSvc,
) -> ContractorProfileResponse:
    """Update the current user's Contractor profile."""
    try:
        profile = await profile_service.update_contractor_profile(current_user, data)
        return ContractorProfileResponse.model_validate(profile)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


# =============================================================================
# Own Profile - User Info
# =============================================================================

@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update own user info",
)
async def update_own_user_info(
    current_user: CurrentUser,
    profile_service: ProfileSvc,
    first_name: str | None = None,
    last_name: str | None = None,
    phone: str | None = None,
    contact_email: str | None = None,
    country: str | None = None,
) -> UserResponse:
    """Update the current user's basic info (name, phone, contact email, country)."""
    user = await profile_service.update_user_info(
        current_user,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        contact_email=contact_email,
        country=country,
    )
    return UserResponse.model_validate(user)


# =============================================================================
# Work Experience CRUD
# =============================================================================

@router.post(
    "/me/work-experiences",
    response_model=WorkExperienceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add work experience",
)
async def add_work_experience(
    data: WorkExperienceCreate,
    current_user: CurrentUser,
    profile_service: ProfileSvc,
) -> WorkExperienceResponse:
    """Add a new work experience entry."""
    try:
        exp = await profile_service.add_work_experience(current_user, data)
        return WorkExperienceResponse.model_validate(exp)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@router.patch(
    "/me/work-experiences/{experience_id}",
    response_model=WorkExperienceResponse,
    summary="Update work experience",
)
async def update_work_experience(
    experience_id: UUID,
    data: WorkExperienceUpdate,
    current_user: CurrentUser,
    profile_service: ProfileSvc,
) -> WorkExperienceResponse:
    """Update an existing work experience entry."""
    try:
        exp = await profile_service.update_work_experience(
            current_user, experience_id, data
        )
        return WorkExperienceResponse.model_validate(exp)
    except (NotFoundError, ValidationError) as e:
        code = status.HTTP_404_NOT_FOUND if isinstance(e, NotFoundError) else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=e.message)


@router.delete(
    "/me/work-experiences/{experience_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete work experience",
)
async def delete_work_experience(
    experience_id: UUID,
    current_user: CurrentUser,
    profile_service: ProfileSvc,
) -> None:
    """Delete a work experience entry."""
    try:
        await profile_service.delete_work_experience(current_user, experience_id)
    except (NotFoundError, ValidationError) as e:
        code = status.HTTP_404_NOT_FOUND if isinstance(e, NotFoundError) else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=e.message)
