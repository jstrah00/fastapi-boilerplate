"""
User model for PostgreSQL with authentication and RBAC support.

Defines the User entity for A2W platform with email/password authentication,
role-based permissions (admin, aretan, contratante), and account management.

Key components:
    - User: SQLAlchemy model with authentication and RBAC fields
    - Roles: admin, aretan, contratante
    - Status: pending, active, inactive, rejected, blocked
    - Login lockout: failed_login_attempts + locked_until

Dependencies:
    - sqlalchemy: ORM and column types
    - app.db.postgres: Base class for models

Related files:
    - app/common/security.py: Password hashing utilities
    - app/common/permissions.py: Role and permission definitions
    - app/schemas/user.py: Pydantic schemas for API
    - app/repositories/user_repo.py: Data access methods
    - app/services/user_service.py: Business logic
"""
from datetime import datetime, UTC
from uuid import UUID, uuid4

from sqlalchemy import String, DateTime, Integer, Boolean
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.postgres import Base


class User(Base):
    """User model for A2W platform authentication with role-based permissions."""

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

    # Status: pending, active, inactive, rejected, blocked
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        index=True,
    )

    # Role: admin, aretan, contratante
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="aretan",
        index=True,
    )

    # Custom permissions beyond role defaults
    custom_permissions: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(100)),
        nullable=True,
        default=None,
    )

    # Contact info (shared across roles)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Profile image
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Location
    country: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True
    )

    # Notification preferences
    email_notifications_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )

    # Terms acceptance
    accepted_terms_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Login lockout
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
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

    # Relationships
    aretan_profile: Mapped["AretanProfile | None"] = relationship(
        "AretanProfile", back_populates="user", uselist=False, lazy="selectin"
    )
    contractor_profile: Mapped["ContractorProfile | None"] = relationship(
        "ContractorProfile", back_populates="user", uselist=False, lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<User {self.email} (role: {self.role}, status: {self.status})>"

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

    @property
    def is_aretan(self) -> bool:
        """Check if user is an Aretan."""
        return self.role == "aretan"

    @property
    def is_contratante(self) -> bool:
        """Check if user is a Contratante."""
        return self.role == "contratante"

    @property
    def is_locked(self) -> bool:
        """Check if account is locked due to failed login attempts."""
        if self.locked_until is None:
            return False
        return datetime.now(UTC) < self.locked_until


# Avoid circular imports - these are imported at module level for type hints
from app.models.postgres.aretan_profile import AretanProfile  # noqa: E402
from app.models.postgres.contractor_profile import ContractorProfile  # noqa: E402
