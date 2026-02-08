"""
Registration endpoints for A2W platform.

Public endpoints for Aretan and Contratante self-registration,
plus avatar upload after registration.
"""
from fastapi import APIRouter, UploadFile, File, status

from app.api.deps import RegistrationSvc, CurrentUser
from app.schemas.registration import AretanRegistration, ContractorRegistration
from app.schemas.user import UserResponse
from app.services.storage_service import get_storage_service

router = APIRouter(prefix="/register", tags=["registration"])


@router.post(
    "/aretan",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_aretan(
    data: AretanRegistration,
    registration_service: RegistrationSvc,
) -> UserResponse:
    """Register a new Aretan user. Status will be 'pending' until admin approval."""
    user = await registration_service.register_aretan(data)
    return UserResponse.model_validate(user)


@router.post(
    "/contratante",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_contractor(
    data: ContractorRegistration,
    registration_service: RegistrationSvc,
) -> UserResponse:
    """Register a new Contratante user. Status will be 'active' immediately."""
    user = await registration_service.register_contractor(data)
    return UserResponse.model_validate(user)


@router.post("/avatar", status_code=status.HTTP_200_OK)
async def upload_avatar(
    current_user: CurrentUser,
    file: UploadFile = File(...),
) -> dict[str, str]:
    """Upload or replace the current user's avatar image (max 1MB, JPEG/PNG/WebP)."""
    storage = get_storage_service()

    # Delete old avatar if exists
    if current_user.avatar_url:
        await storage.delete_file(current_user.avatar_url)

    url = await storage.upload_avatar(file, str(current_user.id))

    # Update user record - handled by the caller committing the session
    current_user.avatar_url = url

    return {"avatar_url": url}
