"""
Refresh Token Blacklist Repository.

Data access layer for refresh token blacklist operations. Handles storing,
querying, and cleaning up used/revoked refresh tokens to enforce single-use
semantics.

Key features:
    - SHA-256 token hashing (tokens never stored in plaintext)
    - Fast blacklist lookups via indexed queries
    - Efficient cleanup of expired tokens
    - Audit trail support (user_id, reason, timestamps)

Dependencies:
    - sqlalchemy: Async ORM operations
    - hashlib: SHA-256 token hashing
    - app.models.postgres.refresh_token_blacklist: Blacklist model
    - app.common.logging: Structured logging

Related files:
    - app/services/auth_service.py: Uses this repo for token rotation
    - app/cli/blacklist.py: Manual cleanup command
    - app/models/postgres/refresh_token_blacklist.py: Data model

Common commands:
    - Manual cleanup: uv run cleanup-blacklist
    - Check blacklist size: psql -c "SELECT COUNT(*) FROM refresh_token_blacklist;"

Example:
    Token rotation flow::

        # In auth_service.py
        async def refresh_access_token(self, refresh_token: str):
            # Check if already used
            is_blacklisted = await blacklist_repo.is_blacklisted(refresh_token)
            if is_blacklisted:
                raise AuthenticationError("Token already used")

            # Add old token to blacklist
            await blacklist_repo.add_to_blacklist(
                token=refresh_token,
                user_id=user.id,
                expires_at=token_expiry,
                reason="used"
            )

            # Generate new tokens...

Security considerations:
    - Tokens hashed with SHA-256 (non-reversible)
    - Index on token_hash for fast lookups
    - Cleanup removes only expired tokens
    - User audit trail for security investigations
"""
import hashlib
from datetime import datetime
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.postgres.refresh_token_blacklist import RefreshTokenBlacklist
from app.common.logging import get_logger

logger = get_logger(__name__)


class RefreshTokenBlacklistRepository:
    """Repository for refresh token blacklist operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

    @staticmethod
    def hash_token(token: str) -> str:
        """
        Hash token using SHA-256 for secure storage.

        Args:
            token: Plaintext refresh token (JWT)

        Returns:
            64-character hex string (SHA-256 hash)

        Example:
            >>> hash_token("eyJhbGciOi...")
            'a1b2c3d4e5f6...'  # 64 hex chars
        """
        return hashlib.sha256(token.encode()).hexdigest()

    async def add_to_blacklist(
        self,
        token: str,
        user_id: UUID,
        expires_at: datetime,
        reason: str = "used",
    ) -> RefreshTokenBlacklist:
        """
        Add a refresh token to the blacklist.

        This prevents the token from being used again (single-use enforcement).

        Args:
            token: The refresh token to blacklist (will be hashed)
            user_id: ID of the user who owns the token
            expires_at: When the token would expire (for cleanup)
            reason: Why it was blacklisted (used, revoked_by_admin, security_incident)

        Returns:
            Created blacklist entry

        Raises:
            IntegrityError: If token already blacklisted (duplicate hash)

        Example:
            >>> await repo.add_to_blacklist(
            ...     token="eyJhbGciOi...",
            ...     user_id=UUID("..."),
            ...     expires_at=datetime(2024, 12, 31),
            ...     reason="used"
            ... )
        """
        token_hash = self.hash_token(token)

        blacklist_entry = RefreshTokenBlacklist(
            token_hash=token_hash,
            user_id=user_id,
            expires_at=expires_at,
            reason=reason,
        )

        self.session.add(blacklist_entry)
        await self.session.commit()

        logger.info(
            "token_blacklisted",
            user_id=str(user_id),
            reason=reason,
            expires_at=expires_at.isoformat(),
        )

        return blacklist_entry

    async def is_blacklisted(self, token: str) -> bool:
        """
        Check if a token is in the blacklist.

        This is called during token refresh to prevent reuse attacks.

        Args:
            token: The refresh token to check (will be hashed)

        Returns:
            True if token is blacklisted, False otherwise

        Example:
            >>> is_blacklisted = await repo.is_blacklisted("eyJhbGciOi...")
            >>> if is_blacklisted:
            ...     raise AuthenticationError("Token already used")
        """
        token_hash = self.hash_token(token)

        stmt = select(RefreshTokenBlacklist).where(
            RefreshTokenBlacklist.token_hash == token_hash
        )
        result = await self.session.execute(stmt)
        entry = result.scalar_one_or_none()

        is_blacklisted = entry is not None

        if is_blacklisted:
            logger.warning(
                "blacklisted_token_check",
                token_hash=token_hash[:16] + "...",  # Log partial hash only
                found=True,
            )

        return is_blacklisted

    async def cleanup_expired(self) -> int:
        """
        Remove expired tokens from blacklist.

        This should be run periodically (manually via CLI) to prevent
        unbounded table growth. Only removes tokens that have expired
        (no longer valid anyway).

        Returns:
            Number of tokens removed

        Example:
            >>> deleted_count = await repo.cleanup_expired()
            >>> print(f"Cleaned up {deleted_count} expired tokens")
            Cleaned up 1234 expired tokens

        Note:
            Run manually with: uv run cleanup-blacklist
            Recommended frequency: Every 1-2 weeks, or when table > 100K rows
        """
        now = datetime.utcnow()

        stmt = delete(RefreshTokenBlacklist).where(
            RefreshTokenBlacklist.expires_at < now
        )
        result = await self.session.execute(stmt)
        await self.session.commit()

        deleted_count = result.rowcount or 0

        if deleted_count > 0:
            logger.info("blacklist_cleanup", deleted_count=deleted_count, timestamp=now.isoformat())

        return deleted_count

    async def revoke_all_user_tokens(self, user_id: UUID) -> int:
        """
        Revoke all refresh tokens for a user (future enhancement).

        This would be useful for:
        - User changes password (invalidate all sessions)
        - Admin suspends account
        - Security incident detected

        Args:
            user_id: User whose tokens should be revoked

        Returns:
            Number of tokens revoked

        Note:
            This is a placeholder for future implementation.
            Currently relies on short token expiration times.
            Full implementation would require storing all active tokens.
        """
        # TODO: Implement if needed
        # Would require tracking all active tokens per user
        # For now, rely on short expiration times (7-30 days)
        logger.warning(
            "revoke_all_not_implemented",
            user_id=str(user_id),
            message="Use short expiration times instead",
        )
        return 0

    async def get_blacklist_stats(self) -> dict[str, int]:
        """
        Get statistics about the blacklist (for monitoring).

        Returns:
            Dictionary with:
                - total: Total blacklisted tokens
                - expired: Tokens that have expired (can be cleaned)
                - active: Tokens still within their expiration window

        Example:
            >>> stats = await repo.get_blacklist_stats()
            >>> print(stats)
            {'total': 15000, 'expired': 5000, 'active': 10000}
        """
        now = datetime.utcnow()

        # Total count
        total_stmt = select(RefreshTokenBlacklist)
        total_result = await self.session.execute(total_stmt)
        total = len(total_result.scalars().all())

        # Expired count
        expired_stmt = select(RefreshTokenBlacklist).where(
            RefreshTokenBlacklist.expires_at < now
        )
        expired_result = await self.session.execute(expired_stmt)
        expired = len(expired_result.scalars().all())

        active = total - expired

        return {"total": total, "expired": expired, "active": active}
