"""
Work experience model for A2W platform.

Stores professional work history entries for Aretan users.

Dependencies:
    - sqlalchemy: ORM and column types
    - app.db.postgres: Base class for models
"""
from datetime import datetime, date, UTC
from uuid import UUID, uuid4

from sqlalchemy import String, Text, Date, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.postgres import Base


class WorkExperience(Base):
    """Work history entry linked to an Aretan profile."""

    __tablename__ = "work_experiences"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    aretan_profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("aretan_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    company: Mapped[str] = mapped_column(String(200), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    # Relationships
    aretan_profile: Mapped["AretanProfile"] = relationship(
        "AretanProfile", back_populates="work_experiences"
    )

    def __repr__(self) -> str:
        return f"<WorkExperience {self.title} at {self.company}>"


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.postgres.aretan_profile import AretanProfile
