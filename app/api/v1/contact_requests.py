"""
Contact request endpoints for PROF-03.

Contractors request contact info from aretans.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.api.deps import CurrentUser, get_db
from app.services.contact_request_service import ContactRequestService
from app.repositories.contact_request_repo import ContactRequestRepository
from app.repositories.user_repo import UserRepository
from app.services.notification_service import NotificationService
from app.repositories.notification_repo import NotificationRepository
from app.schemas.contact_request import (
    ContactRequestCreate,
    ContactRequestUpdate,
    ContactRequestResponse,
    ContactRequestListResponse,
)
from app.common.exceptions import NotFoundError, ValidationError, AlreadyExistsError
from app.common.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/contact-requests", tags=["contact-requests"])


async def get_contact_request_service(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> ContactRequestService:
    """Get contact request service instance."""
    return ContactRequestService(
        ContactRequestRepository(db),
        UserRepository(db),
        NotificationService(NotificationRepository(db)),
    )


ContactRequestSvc = Annotated[
    ContactRequestService, Depends(get_contact_request_service)
]


@router.post(
    "/",
    response_model=ContactRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Request contact info",
)
async def create_contact_request(
    data: ContactRequestCreate,
    service: ContactRequestSvc,
    current_user: CurrentUser,
) -> ContactRequestResponse:
    """Create a contact request (contractor -> aretan)."""
    try:
        return await service.create_request(data, current_user)
    except (ValidationError, AlreadyExistsError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.get(
    "/received",
    response_model=ContactRequestListResponse,
    summary="Get received requests",
)
async def get_received_requests(
    service: ContactRequestSvc,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> ContactRequestListResponse:
    """Get contact requests received by current user."""
    return await service.get_received_requests(current_user, skip, limit)


@router.get(
    "/sent",
    response_model=ContactRequestListResponse,
    summary="Get sent requests",
)
async def get_sent_requests(
    service: ContactRequestSvc,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> ContactRequestListResponse:
    """Get contact requests sent by current user."""
    return await service.get_sent_requests(current_user, skip, limit)


@router.patch(
    "/{request_id}",
    response_model=ContactRequestResponse,
    summary="Respond to contact request",
)
async def update_contact_request(
    request_id: UUID,
    data: ContactRequestUpdate,
    service: ContactRequestSvc,
    current_user: CurrentUser,
) -> ContactRequestResponse:
    """Accept or reject a contact request."""
    try:
        return await service.update_request(request_id, data, current_user)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
