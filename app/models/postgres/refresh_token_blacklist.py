"""
Refresh Token Blacklist Model.

Tracks used and revoked refresh tokens to prevent token reuse attacks.
When a refresh token is used to generate new tokens, its hash is added to this
blacklist to ensure single-use semantics.

Key features:
    - Stores SHA-256 hash of tokens (not plaintext)
    - Tracks user_id for audit trails
    - Includes expiration time for efficient cleanup
    - Supports multiple blacklist reasons (used, revoked, security)

Dependencies:
    - app.models.postgres.base: SQLAlchemy Base class
    - sqlalchemy: ORM functionality

Related files:
    - app/repositories/refresh_token_blacklist_repository.py: Data access layer
    - app/services/auth_service.py: Token rotation logic
    - app/cli/blacklist.py: Manual cleanup command

Common commands:
    - Cleanup expired tokens: uv run cleanup-blacklist
    - Check table size: psql -c "SELECT COUNT(*) FROM refresh_token_blacklist;"

Example:
    Token rotation flow::

        # User refreshes access token
        POST /api/v1/auth/refresh

        # Backend:
        1. Validates refresh token
        2. Checks if token_hash in blacklist (prevents reuse)
        3. Adds old token hash to blacklist
        4. Generates new access + refresh tokens
        5. Returns new tokens

Security considerations:
    - Only token hash stored (not recoverable)
    - Single-use tokens prevent stolen token reuse
    - Manual cleanup prevents unbounded table growth
"""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import String, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base


class RefreshTokenBlacklist(Base):
    """
    Blacklist for used/revoked refresh tokens.

    When a refresh token is used, its hash is added here to prevent reuse.
    This implements single-use refresh tokens for enhanced security.

    Attributes:
        id: Unique identifier for blacklist entry
        token_hash: SHA-256 hash of the refresh token (64 hex chars)
        user_id: ID of user who owned the token (for audit trails)
        blacklisted_at: Timestamp when token was blacklisted
        expires_at: When token would have expired (for cleanup queries)
        reason: Why token was blacklisted (used, revoked_by_admin, security_incident)

    Indexes:
        - token_hash: Fast lookups during refresh validation
        - expires_at: Efficient cleanup of expired tokens
        - (token_hash, expires_at): Composite index for validation + cleanup
        - (user_id, blacklisted_at): Audit trail queries
    """

    __tablename__ = "refresh_token_blacklist"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # SHA-256 hash of the refresh token (not stored in plaintext)
    token_hash: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )

    # User who owned the token
    user_id: Mapped[UUID] = mapped_column(nullable=False, index=True)

    # When token was blacklisted
    blacklisted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    # When token would have expired (for cleanup)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    # Why it was blacklisted (used, revoked_by_admin, security_incident, etc.)
    reason: Mapped[str] = mapped_column(String(50), default="used", nullable=False)

    # Indexes for performance
    __table_args__ = (
        Index("ix_token_hash_expires", "token_hash", "expires_at"),
        Index("ix_user_blacklisted", "user_id", "blacklisted_at"),
    )

    def __repr__(self) -> str:
        """String representation of blacklist entry."""
        return f"<RefreshTokenBlacklist(user_id={self.user_id}, reason={self.reason}, blacklisted_at={self.blacklisted_at})>"
