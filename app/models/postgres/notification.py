"""
Notification model for in-app notifications.

Tracks likes, comments, and mentions so users see activity on their content.
"""
from datetime import datetime, UTC
from uuid import UUID, uuid4

from sqlalchemy import String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.postgres import Base


class Notification(Base):
    """In-app notification for a user."""

    __tablename__ = "notifications"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    actor_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # "like", "comment", "mention"
    post_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"), nullable=True
    )
    comment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("comments.id", ondelete="CASCADE"), nullable=True
    )
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User", foreign_keys=[user_id], lazy="noload"
    )
    actor: Mapped["User"] = relationship(
        "User", foreign_keys=[actor_id], lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Notification {self.type} for {self.user_id}>"


from app.models.postgres.user import User  # noqa: E402
