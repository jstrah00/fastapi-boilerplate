"""
Aretan profile model for A2W platform.

Extended profile data for users with role=aretan, including sport achievements,
professional info, employment status, and contact visibility settings.

Dependencies:
    - sqlalchemy: ORM and column types
    - app.db.postgres: Base class for models
"""
from datetime import datetime, UTC
from uuid import UUID, uuid4

from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.postgres import Base


class AretanProfile(Base):
    """Extended profile for Aretan users (sport talent)."""

    __tablename__ = "aretan_profiles"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # Lookups
    industry_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("master_industries.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    profession_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("master_professions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    max_achievement_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("master_sport_achievements.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Free text
    sport_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    professional_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Employment: employed, independent, open, unspecified
    employment_status: Mapped[str | None] = mapped_column(
        String(30), nullable=True, index=True
    )

    # Multi-select stored as array
    languages: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(50)), nullable=True
    )

    # Social networks as JSON: {"linkedin": "url", "instagram": "url", ...}
    social_networks: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Contact visibility
    phone_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    email_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="aretan_profile")
    industry: Mapped["MasterIndustry | None"] = relationship("MasterIndustry", lazy="selectin")
    profession: Mapped["MasterProfession | None"] = relationship("MasterProfession", lazy="selectin")
    max_achievement: Mapped["MasterSportAchievement | None"] = relationship(
        "MasterSportAchievement", lazy="selectin"
    )
    work_experiences: Mapped[list["WorkExperience"]] = relationship(
        "WorkExperience", back_populates="aretan_profile", lazy="selectin",
        order_by="WorkExperience.display_order",
    )

    def __repr__(self) -> str:
        return f"<AretanProfile user_id={self.user_id}>"


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.postgres.user import User
    from app.models.postgres.master_tables import (
        MasterIndustry,
        MasterProfession,
        MasterSportAchievement,
    )
    from app.models.postgres.work_experience import WorkExperience
