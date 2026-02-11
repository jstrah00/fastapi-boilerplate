"""
Contact request service for PROF-03.

Business logic for contractor-aretan contact requests.
"""
from uuid import UUID

from app.models.postgres.user import User
from app.models.postgres.contact_request import ContactRequest
from app.repositories.contact_request_repo import ContactRequestRepository
from app.repositories.user_repo import UserRepository
from app.services.notification_service import NotificationService
from app.schemas.contact_request import (
    ContactRequestCreate,
    ContactRequestUpdate,
    ContactRequestResponse,
    ContactRequestListResponse,
)
from app.schemas.post import PostAuthor
from app.common.exceptions import NotFoundError, ValidationError, AlreadyExistsError
from app.common.logging import get_logger
from app.services import email_service

logger = get_logger(__name__)


class ContactRequestService:
    """Service for contact request business logic."""

    def __init__(
        self,
        request_repo: ContactRequestRepository,
        user_repo: UserRepository,
        notification_service: NotificationService,
    ):
        self.request_repo = request_repo
        self.user_repo = user_repo
        self.notification_service = notification_service

    async def create_request(
        self, data: ContactRequestCreate, requester: User
    ) -> ContactRequestResponse:
        """Create a contact request from contractor to aretan."""
        # Only contractors can request
        if requester.role != "contratante":
            raise ValidationError(
                message="Only contractors can request contact information"
            )

        # Target must exist and be an aretan
        target = await self.user_repo.get(data.target_id)
        if not target or target.role != "aretan":
            raise NotFoundError(message="Target user not found or not an aretan")

        # Check for existing request
        existing = await self.request_repo.get_by_users(requester.id, data.target_id)
        if existing:
            raise AlreadyExistsError(message="Contact request already exists")

        # Create request
        request = ContactRequest(
            requester_id=requester.id,
            target_id=data.target_id,
            message=data.message,
            status="pending",
        )
        request = await self.request_repo.create(request)

        # Reload for relationships
        request = await self.request_repo.get(request.id)

        # Notify target user
        await self.notification_service.create_notification(
            user_id=data.target_id,
            actor_id=requester.id,
            notification_type="contact_request",
        )

        logger.info(
            "contact_request_created",
            requester=str(requester.id),
            target=str(data.target_id),
        )

        # Email the aretan about the new contact request (non-blocking)
        try:
            await email_service.send_contact_request(
                to_email=target.email,
                first_name=target.first_name,
                requester_name=f"{requester.first_name} {requester.last_name}",
                message=data.message,
            )
        except Exception as e:
            logger.warning("email_send_failed", error=str(e), type="contact_request")

        return self._to_response(request)

    async def update_request(
        self, request_id: UUID, data: ContactRequestUpdate, user: User
    ) -> ContactRequestResponse:
        """Accept or reject a contact request (target only)."""
        request = await self.request_repo.get(request_id)
        if not request:
            raise NotFoundError(message="Contact request not found")

        # Only target can respond
        if request.target_id != user.id:
            raise ValidationError(message="Only the target can respond to this request")

        # Can only update pending requests
        if request.status != "pending":
            raise ValidationError(message="Request has already been responded to")

        # Update status
        request = await self.request_repo.update(request_id, {"status": data.status})

        # Notify requester
        notification_type = (
            "contact_accepted" if data.status == "accepted" else "contact_rejected"
        )
        # Include contact info when accepted
        extra_data = None
        if data.status == "accepted":
            extra_data = {}
            if user.email:
                extra_data["email"] = user.email
            if user.phone:
                extra_data["phone"] = user.phone

        await self.notification_service.create_notification(
            user_id=request.requester_id,
            actor_id=user.id,
            notification_type=notification_type,
            extra_data=extra_data or None,
        )

        logger.info(
            "contact_request_updated",
            request_id=str(request_id),
            status=data.status,
        )

        # Email the contractor when their request is accepted (non-blocking)
        if data.status == "accepted":
            requester = await self.user_repo.get(request.requester_id)
            if requester:
                try:
                    await email_service.send_contact_accepted(
                        to_email=requester.email,
                        first_name=requester.first_name,
                        aretan_name=f"{user.first_name} {user.last_name}",
                        contact_email=user.email,
                        phone=user.phone,
                    )
                except Exception as e:
                    logger.warning("email_send_failed", error=str(e), type="contact_accepted")

        return self._to_response(request)

    async def get_received_requests(
        self, user: User, skip: int = 0, limit: int = 20
    ) -> ContactRequestListResponse:
        """Get requests received by current user."""
        requests = await self.request_repo.get_received_requests(
            user.id, skip, limit
        )
        total = await self.request_repo.count_received(user.id)

        return ContactRequestListResponse(
            requests=[self._to_response(r) for r in requests],
            total=total,
        )

    async def get_sent_requests(
        self, user: User, skip: int = 0, limit: int = 20
    ) -> ContactRequestListResponse:
        """Get requests sent by current user."""
        requests = await self.request_repo.get_sent_requests(
            user.id, skip, limit
        )
        total = await self.request_repo.count_sent(user.id)

        return ContactRequestListResponse(
            requests=[self._to_response(r) for r in requests],
            total=total,
        )

    def _to_response(self, request: ContactRequest) -> ContactRequestResponse:
        """Convert model to response schema."""
        # Include target's contact info when request is accepted
        contact_email = None
        phone = None
        if request.status == "accepted":
            contact_email = request.target.email
            phone = request.target.phone

        return ContactRequestResponse(
            id=request.id,
            requester=PostAuthor(
                id=request.requester.id,
                first_name=request.requester.first_name,
                last_name=request.requester.last_name,
                avatar_url=request.requester.avatar_url,
                role=request.requester.role,
            ),
            target=PostAuthor(
                id=request.target.id,
                first_name=request.target.first_name,
                last_name=request.target.last_name,
                avatar_url=request.target.avatar_url,
                role=request.target.role,
            ),
            status=request.status,
            message=request.message,
            contact_email=contact_email,
            phone=phone,
            created_at=request.created_at,
            updated_at=request.updated_at,
        )
