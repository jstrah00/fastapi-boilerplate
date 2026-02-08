"""
Master list models for A2W platform.

Configurable lookup tables managed by admins: industries (rubros),
professions, and sport achievements. Used as foreign keys in profiles.

Dependencies:
    - sqlalchemy: ORM and column types
    - app.db.postgres: Base class for models
"""
from datetime import datetime, UTC
from uuid import UUID, uuid4

from sqlalchemy import String, Boolean, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base


class MasterIndustry(Base):
    """Industry/Rubro lookup table managed by admins."""

    __tablename__ = "master_industries"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    def __repr__(self) -> str:
        return f"<MasterIndustry {self.name}>"


class MasterProfession(Base):
    """Profession lookup table managed by admins."""

    __tablename__ = "master_professions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    def __repr__(self) -> str:
        return f"<MasterProfession {self.name}>"


class MasterSportAchievement(Base):
    """Sport achievement level lookup table managed by admins."""

    __tablename__ = "master_sport_achievements"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    def __repr__(self) -> str:
        return f"<MasterSportAchievement {self.name}>"
