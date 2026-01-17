"""
User model for PostgreSQL.

# =============================================================================
# EXAMPLE MODEL: This is an example User model demonstrating SQLAlchemy usage.
# Customize this model based on your project's authentication requirements.
# =============================================================================
"""
from datetime import datetime, UTC
from uuid import UUID, uuid4

from sqlalchemy import String, DateTime
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base


class User(Base):
    """
    User model for authentication with role-based permissions.

    # EXAMPLE: User model with email/password authentication and RBAC.
    # Customize fields based on your project requirements.
    #
    # Common additions you might want:
    # - phone_number: For SMS verification
    # - avatar_url: For profile pictures
    # - preferences: JSON field for user settings
    # - organization_id: For multi-tenant applications
    """

    __tablename__ = "users"

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Basic info
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Authentication
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # OPTIONAL: OAuth support - uncomment if needed
    # google_id: Mapped[str | None] = mapped_column(
    #     String(255), unique=True, index=True, nullable=True
    # )

    # Status: invited, active, inactive
    # - invited: User was invited but hasn't set password yet
    # - active: Normal active user
    # - inactive: Soft-deleted or suspended user
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        index=True,
    )

    # ==========================================================================
    # Role-Based Access Control (RBAC)
    # See app/core/permissions.py for role and permission definitions
    # ==========================================================================

    # User role - determines base permissions
    # Values should match Role enum in app/core/permissions.py
    # Default roles: "admin", "user"
    # CUSTOMIZATION: Add more roles like "manager", "moderator", etc.
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="user",
        index=True,
    )

    # Custom permissions - additional permissions beyond role defaults
    # This allows granting specific permissions without changing roles
    # Stored as an array of permission strings (e.g., ["users:read", "items:delete"])
    # CUSTOMIZATION: Use this for fine-grained permission control
    custom_permissions: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(100)),
        nullable=True,
        default=None,
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
        return f"<User {self.email} (role: {self.role})>"

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def is_active(self) -> bool:
        """Check if user is active."""
        return self.status == "active"

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == "admin"
