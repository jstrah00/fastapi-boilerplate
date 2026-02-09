"""
Contact request model for contractor-aretan connections.

Allows contractors to request contact information from aretans.
"""
from datetime import datetime, UTC
from uuid import UUID, uuid4

from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.postgres import Base


class ContactRequest(Base):
    """Contact request from contractor to aretan."""

    __tablename__ = "contact_requests"

    __table_args__ = (
        UniqueConstraint("requester_id", "target_id", name="uq_contact_request"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    requester_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # "pending", "accepted", "rejected"
    message: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    requester: Mapped["User"] = relationship(
        "User", foreign_keys=[requester_id], lazy="selectin"
    )
    target: Mapped["User"] = relationship(
        "User", foreign_keys=[target_id], lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<ContactRequest {self.status} from {self.requester_id} to {self.target_id}>"


from app.models.postgres.user import User  # noqa: E402
