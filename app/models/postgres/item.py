"""
Item model for PostgreSQL - CRUD resource example.

Demonstrates a standard CRUD resource with ownership, soft delete, and timestamps.
Use this as a template for creating your own domain models.

Key components:
    - Item: SQLAlchemy model for a user-owned resource
    - owner_id: Foreign key linking to users table
    - status: Soft delete support (active/inactive)
    - created_at/updated_at: Automatic timestamps

Dependencies:
    - sqlalchemy: ORM and column types
    - app.db.postgres: Base class for models

Related files:
    - app/schemas/item.py: Pydantic schemas for API
    - app/repositories/item_repo.py: Data access methods
    - app/services/item_service.py: Business logic
    - app/api/v1/items.py: API endpoints

Common commands:
    - Create migration: uv run alembic revision --autogenerate -m "update items"
    - Apply migration: uv run alembic upgrade head

Example:
    Creating an item::

        from app.models.postgres.item import Item

        item = Item(
            title="My Item",
            description="Item description",
            owner_id=user.id,
            status="active",
        )
        session.add(item)
        await session.commit()

    Querying items::

        from sqlalchemy import select

        # Get active items for a user
        result = await session.execute(
            select(Item)
            .where(Item.owner_id == user_id)
            .where(Item.status == "active")
        )
        items = result.scalars().all()
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
