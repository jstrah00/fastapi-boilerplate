"""
Contractor profile model for A2W platform.

Extended profile data for users with role=contratante, including company info,
entity type, and industry classification.

Dependencies:
    - sqlalchemy: ORM and column types
    - app.db.postgres: Base class for models
"""
from datetime import datetime, UTC
from uuid import UUID, uuid4

from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.postgres import Base


class ContractorProfile(Base):
    """Extended profile for Contratante users (companies/hirers)."""

    __tablename__ = "contractor_profiles"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # Entity type: individual or company
    entity_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="company"
    )

    # Company info
    company_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    company_size: Mapped[str | None] = mapped_column(String(50), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Industry
    industry_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("master_industries.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Description
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

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
    user: Mapped["User"] = relationship("User", back_populates="contractor_profile")
    industry: Mapped["MasterIndustry | None"] = relationship("MasterIndustry", lazy="selectin")

    def __repr__(self) -> str:
        return f"<ContractorProfile user_id={self.user_id}>"


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.postgres.user import User
    from app.models.postgres.master_tables import MasterIndustry
