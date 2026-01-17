"""
Item model for PostgreSQL - CRUD Example.

# =============================================================================
# EXAMPLE MODEL: This demonstrates a simple CRUD resource model.
# Use this as a template for creating your own domain models.
# You can rename or delete this file based on your project needs.
# =============================================================================
"""
from datetime import datetime, UTC
from uuid import UUID, uuid4

from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base


class Item(Base):
    """
    Example Item model demonstrating a basic CRUD resource.

    # EXAMPLE: Replace this with your actual domain models.
    # This demonstrates:
    # - UUID primary key
    # - Foreign key relationship (owner_id -> users)
    # - Timestamps
    # - Soft delete pattern (status field)
    """

    __tablename__ = "items"

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Item data
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Owner relationship
    # NOTE: This creates a foreign key to the users table
    owner_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Status for soft delete: active, inactive
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        index=True,
    )

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

    def __repr__(self) -> str:
        return f"<Item {self.title}>"

    @property
    def is_active(self) -> bool:
        """Check if item is active."""
        return self.status == "active"
