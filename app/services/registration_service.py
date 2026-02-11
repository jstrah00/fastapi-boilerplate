"""
Registration service for A2W platform.

Handles differentiated registration for Aretan and Contratante users,
including profile creation, work experience, and validation.
"""
from datetime import datetime, UTC

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.postgres.user import User
from app.models.postgres.aretan_profile import AretanProfile
from app.models.postgres.contractor_profile import ContractorProfile
from app.models.postgres.work_experience import WorkExperience
from app.repositories.user_repo import UserRepository
from app.schemas.registration import AretanRegistration, ContractorRegistration
from app.common.security import get_password_hash
from app.common.logging import get_logger
from app.common.exceptions import AlreadyExistsError
from app.services import email_service

logger = get_logger(__name__)


class RegistrationService:
    """Service for user registration business logic."""

    def __init__(self, db: AsyncSession, user_repo: UserRepository):
        """Initialize with database session and user repository."""
        self.db = db
        self.user_repo = user_repo

    async def register_aretan(self, data: AretanRegistration) -> User:
        """Register a new Aretan user with profile and work experiences."""
        # Check email uniqueness (also block rejected emails from re-registering)
        existing = await self.user_repo.get_by_email(data.email)
        if existing:
            if existing.status == "rejected":
                raise AlreadyExistsError(
                    message="This email has been previously rejected and cannot be used for registration",
                    details={"email": data.email},
                )
            raise AlreadyExistsError(
                message="A user with this email already exists",
                details={"email": data.email},
            )

        # Create user (status=pending for Aretans)
        user = User(
            email=data.email,
            first_name=data.first_name,
            last_name=data.last_name,
            password_hash=get_password_hash(data.password),
            role="aretan",
            status="pending",
            phone=data.phone,
            country=data.country,
            accepted_terms_at=datetime.now(UTC),
        )
        self.db.add(user)
        await self.db.flush()

        # Create aretan profile
        profile = AretanProfile(
            user_id=user.id,
            industry_ids=data.industry_ids,
            profession_ids=data.profession_ids,
            max_achievement_id=data.max_achievement_id,
            sport_description=data.sport_description,
            professional_description=data.professional_description,
            employment_status=data.employment_status,
            languages=data.languages,
            social_networks=data.social_networks,
            phone_visible=False,
            email_visible=False,
        )
        self.db.add(profile)
        await self.db.flush()

        # Create work experiences
        for i, exp_data in enumerate(data.work_experiences):
            experience = WorkExperience(
                aretan_profile_id=profile.id,
                title=exp_data.title,
                company=exp_data.company,
                start_date=exp_data.start_date,
                end_date=exp_data.end_date,
                description=exp_data.description,
                display_order=exp_data.display_order or i,
            )
            self.db.add(experience)

        await self.db.flush()
        await self.db.refresh(user)

        logger.info(
            "aretan_registered",
            user_id=str(user.id),
            email=user.email,
            status="pending",
        )

        await email_service.send_welcome_aretan(user.email, user.first_name)

        return user

    async def register_contractor(self, data: ContractorRegistration) -> User:
        """Register a new Contratante user with profile."""
        # Check email uniqueness (also block rejected emails from re-registering)
        existing = await self.user_repo.get_by_email(data.email)
        if existing:
            if existing.status == "rejected":
                raise AlreadyExistsError(
                    message="This email has been previously rejected and cannot be used for registration",
                    details={"email": data.email},
                )
            raise AlreadyExistsError(
                message="A user with this email already exists",
                details={"email": data.email},
            )

        # Create user (status=active for Contratantes)
        user = User(
            email=data.email,
            first_name=data.first_name,
            last_name=data.last_name,
            password_hash=get_password_hash(data.password),
            role="contratante",
            status="active",
            phone=data.phone,
            country=data.country,
            accepted_terms_at=datetime.now(UTC),
        )
        self.db.add(user)
        await self.db.flush()

        # Create contractor profile
        profile = ContractorProfile(
            user_id=user.id,
            entity_type=data.entity_type,
            company_name=data.company_name,
            company_size=data.company_size,
            website=data.website,
            industry_id=data.industry_id,
            description=data.description,
        )
        self.db.add(profile)
        await self.db.flush()
        await self.db.refresh(user)

        logger.info(
            "contractor_registered",
            user_id=str(user.id),
            email=user.email,
            status="active",
        )

        await email_service.send_welcome_contractor(user.email, user.first_name)

        return user
