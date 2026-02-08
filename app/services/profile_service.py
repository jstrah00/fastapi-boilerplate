"""
Profile service for A2W platform.

Business logic for viewing and editing Aretan and Contratante profiles,
including work experience management and contact visibility rules.
"""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.postgres.user import User
from app.models.postgres.aretan_profile import AretanProfile
from app.models.postgres.contractor_profile import ContractorProfile
from app.models.postgres.work_experience import WorkExperience
from app.schemas.profile import (
    AretanProfileUpdate,
    ContractorProfileUpdate,
    WorkExperienceCreate,
    WorkExperienceUpdate,
    PublicUserInfo,
    AretanPublicProfile,
    ContractorPublicProfile,
    AretanProfileResponse,
    ContractorProfileResponse,
    UnifiedPublicProfile,
)
from app.common.logging import get_logger
from app.common.exceptions import NotFoundError, ValidationError

logger = get_logger(__name__)


class ProfileService:
    """Service for profile business logic."""

    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db

    # =========================================================================
    # Public Profile Views
    # =========================================================================

    async def get_aretan_profile(
        self, user_id: UUID, viewer: User | None = None
    ) -> AretanPublicProfile:
        """Get public profile for an Aretan user, applying visibility rules."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user or user.role != "aretan":
            raise NotFoundError(
                message="Aretan profile not found",
                details={"user_id": str(user_id)},
            )

        if not user.aretan_profile:
            raise NotFoundError(
                message="Profile data not found",
                details={"user_id": str(user_id)},
            )

        profile = user.aretan_profile

        # Apply contact visibility rules
        is_owner = viewer and viewer.id == user_id
        is_admin = viewer and viewer.is_admin

        user_info = PublicUserInfo(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            avatar_url=user.avatar_url,
            country=user.country,
            role=user.role,
            status=user.status,
            phone=user.phone if (is_owner or is_admin or profile.phone_visible) else None,
            contact_email=user.contact_email if (is_owner or is_admin or profile.email_visible) else None,
        )

        return AretanPublicProfile(
            user=user_info,
            profile=AretanProfileResponse.model_validate(profile),
        )

    async def get_contractor_profile(
        self, user_id: UUID, viewer: User | None = None
    ) -> ContractorPublicProfile:
        """Get public profile for a Contractor user."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user or user.role != "contratante":
            raise NotFoundError(
                message="Contractor profile not found",
                details={"user_id": str(user_id)},
            )

        if not user.contractor_profile:
            raise NotFoundError(
                message="Profile data not found",
                details={"user_id": str(user_id)},
            )

        user_info = PublicUserInfo(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            avatar_url=user.avatar_url,
            country=user.country,
            role=user.role,
            status=user.status,
            phone=user.phone,
            contact_email=user.contact_email,
        )

        return ContractorPublicProfile(
            user=user_info,
            profile=ContractorProfileResponse.model_validate(user.contractor_profile),
        )

    async def get_public_profile(
        self, user_id: UUID, viewer: User | None = None
    ) -> UnifiedPublicProfile:
        """Get unified public profile for any user, regardless of role."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError(
                message="User not found",
                details={"user_id": str(user_id)},
            )

        is_owner = viewer and viewer.id == user_id
        is_admin = viewer and viewer.is_admin

        aretan_response = None
        contractor_response = None

        if user.role == "aretan" and user.aretan_profile:
            profile = user.aretan_profile
            user_info = PublicUserInfo(
                id=user.id,
                first_name=user.first_name,
                last_name=user.last_name,
                avatar_url=user.avatar_url,
                country=user.country,
                role=user.role,
                status=user.status,
                phone=user.phone if (is_owner or is_admin or profile.phone_visible) else None,
                contact_email=user.contact_email if (is_owner or is_admin or profile.email_visible) else None,
            )
            aretan_response = AretanProfileResponse.model_validate(profile)
        elif user.role == "contratante" and user.contractor_profile:
            user_info = PublicUserInfo(
                id=user.id,
                first_name=user.first_name,
                last_name=user.last_name,
                avatar_url=user.avatar_url,
                country=user.country,
                role=user.role,
                status=user.status,
                phone=user.phone,
                contact_email=user.contact_email,
            )
            contractor_response = ContractorProfileResponse.model_validate(
                user.contractor_profile
            )
        else:
            user_info = PublicUserInfo(
                id=user.id,
                first_name=user.first_name,
                last_name=user.last_name,
                avatar_url=user.avatar_url,
                country=user.country,
                role=user.role,
                status=user.status,
                phone=None,
                contact_email=None,
            )

        return UnifiedPublicProfile(
            user=user_info,
            aretan_profile=aretan_response,
            contractor_profile=contractor_response,
        )

    # =========================================================================
    # Profile Updates (own profile only)
    # =========================================================================

    async def update_aretan_profile(
        self, user: User, data: AretanProfileUpdate
    ) -> AretanProfile:
        """Update the current user's Aretan profile."""
        if not user.aretan_profile:
            raise NotFoundError(
                message="Aretan profile not found",
                details={"user_id": str(user.id)},
            )

        profile = user.aretan_profile
        update_dict = data.model_dump(exclude_unset=True)

        for key, value in update_dict.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        await self.db.flush()
        await self.db.refresh(profile)

        logger.info("aretan_profile_updated", user_id=str(user.id))
        return profile

    async def update_contractor_profile(
        self, user: User, data: ContractorProfileUpdate
    ) -> ContractorProfile:
        """Update the current user's Contractor profile."""
        if not user.contractor_profile:
            raise NotFoundError(
                message="Contractor profile not found",
                details={"user_id": str(user.id)},
            )

        profile = user.contractor_profile
        update_dict = data.model_dump(exclude_unset=True)

        for key, value in update_dict.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        await self.db.flush()
        await self.db.refresh(profile)

        logger.info("contractor_profile_updated", user_id=str(user.id))
        return profile

    # =========================================================================
    # User basic info update
    # =========================================================================

    async def update_user_info(
        self,
        user: User,
        first_name: str | None = None,
        last_name: str | None = None,
        phone: str | None = None,
        contact_email: str | None = None,
        country: str | None = None,
    ) -> User:
        """Update basic user info fields."""
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if phone is not None:
            user.phone = phone
        if contact_email is not None:
            user.contact_email = contact_email
        if country is not None:
            user.country = country

        await self.db.flush()
        await self.db.refresh(user)

        logger.info("user_info_updated", user_id=str(user.id))
        return user

    # =========================================================================
    # Work Experience CRUD
    # =========================================================================

    async def add_work_experience(
        self, user: User, data: WorkExperienceCreate
    ) -> WorkExperience:
        """Add a work experience entry to the user's Aretan profile."""
        if not user.aretan_profile:
            raise ValidationError(
                message="Only Aretan users can have work experiences",
                details={"user_id": str(user.id)},
            )

        experience = WorkExperience(
            aretan_profile_id=user.aretan_profile.id,
            title=data.title,
            company=data.company,
            start_date=data.start_date,
            end_date=data.end_date,
            description=data.description,
            display_order=data.display_order,
        )
        self.db.add(experience)
        await self.db.flush()
        await self.db.refresh(experience)

        logger.info(
            "work_experience_added",
            user_id=str(user.id),
            experience_id=str(experience.id),
        )
        return experience

    async def update_work_experience(
        self, user: User, experience_id: UUID, data: WorkExperienceUpdate
    ) -> WorkExperience:
        """Update a work experience entry."""
        experience = await self._get_own_experience(user, experience_id)

        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if hasattr(experience, key):
                setattr(experience, key, value)

        await self.db.flush()
        await self.db.refresh(experience)

        logger.info(
            "work_experience_updated",
            user_id=str(user.id),
            experience_id=str(experience_id),
        )
        return experience

    async def delete_work_experience(
        self, user: User, experience_id: UUID
    ) -> None:
        """Delete a work experience entry."""
        experience = await self._get_own_experience(user, experience_id)
        await self.db.delete(experience)
        await self.db.flush()

        logger.info(
            "work_experience_deleted",
            user_id=str(user.id),
            experience_id=str(experience_id),
        )

    async def _get_own_experience(
        self, user: User, experience_id: UUID
    ) -> WorkExperience:
        """Get a work experience that belongs to the user."""
        if not user.aretan_profile:
            raise ValidationError(
                message="Only Aretan users can manage work experiences",
                details={"user_id": str(user.id)},
            )

        result = await self.db.execute(
            select(WorkExperience).where(
                WorkExperience.id == experience_id,
                WorkExperience.aretan_profile_id == user.aretan_profile.id,
            )
        )
        experience = result.scalar_one_or_none()
        if not experience:
            raise NotFoundError(
                message="Work experience not found",
                details={"experience_id": str(experience_id)},
            )
        return experience
