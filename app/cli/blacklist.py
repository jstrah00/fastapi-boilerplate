"""
Manual command to cleanup expired tokens from blacklist.

This command removes expired refresh tokens from the blacklist table
to prevent unbounded growth. Should be run periodically (every 1-2 weeks).

Key features:
    - Removes only expired tokens (safe operation)
    - Logs deletion count
    - Returns exit code 0 on success

Dependencies:
    - asyncio: Async operation support
    - app.db.postgres: Database session
    - app.repositories.refresh_token_blacklist_repository: Blacklist operations
    - app.common.logging: Structured logging

Related files:
    - app/repositories/refresh_token_blacklist_repository.py: Cleanup logic
    - app/models/postgres/refresh_token_blacklist.py: Data model
    - pyproject.toml: Command registration

Common commands:
    - Run cleanup: uv run cleanup-blacklist
    - Check before: psql -c "SELECT COUNT(*) FROM refresh_token_blacklist;"
    - Check after: psql -c "SELECT COUNT(*) FROM refresh_token_blacklist WHERE expires_at < NOW();"

Example:
    Manual cleanup::

        $ uv run cleanup-blacklist
        2024-01-15 10:30:00 - INFO - blacklist_cleanup_started
        2024-01-15 10:30:01 - INFO - blacklist_cleanup_completed deleted_count=1234
        ✅ Cleanup completed: 1234 expired tokens removed

Recommended frequency:
    - Run every 1-2 weeks
    - Or when table size exceeds 100,000 rows
    - Monitor with: SELECT COUNT(*) FROM refresh_token_blacklist;

Security considerations:
    - Only removes expired tokens (no data loss risk)
    - Uses database transaction (atomic operation)
    - Logs all operations for audit trail
"""
import asyncio
import sys
from datetime import datetime

from app.db.postgres import async_session_maker
from app.repositories.refresh_token_blacklist_repository import (
    RefreshTokenBlacklistRepository,
)
from app.common.logging import get_logger

logger = get_logger(__name__)


async def cleanup_expired_tokens() -> int:
    """
    Remove expired tokens from blacklist.

    Returns:
        Number of tokens removed

    Example:
        >>> deleted = await cleanup_expired_tokens()
        >>> print(f"Removed {deleted} tokens")
    """
    logger.info("blacklist_cleanup_started", timestamp=datetime.utcnow().isoformat())

    try:
        async with async_session_maker() as session:
            repo = RefreshTokenBlacklistRepository(session)

            # Get stats before cleanup
            stats_before = await repo.get_blacklist_stats()
            logger.info(
                "blacklist_stats_before",
                total=stats_before["total"],
                expired=stats_before["expired"],
                active=stats_before["active"],
            )

            # Perform cleanup
            deleted_count = await repo.cleanup_expired()

            # Get stats after cleanup
            stats_after = await repo.get_blacklist_stats()
            logger.info(
                "blacklist_stats_after",
                total=stats_after["total"],
                expired=stats_after["expired"],
                active=stats_after["active"],
            )

            logger.info(
                "blacklist_cleanup_completed",
                deleted_count=deleted_count,
                timestamp=datetime.utcnow().isoformat(),
            )

            print(f"✅ Cleanup completed: {deleted_count} expired tokens removed")
            print(f"   Before: {stats_before['total']} total ({stats_before['expired']} expired)")
            print(f"   After:  {stats_after['total']} total ({stats_after['expired']} expired)")

            return deleted_count

    except Exception as e:
        logger.error(
            "blacklist_cleanup_failed",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
        print(f"❌ Cleanup failed: {str(e)}", file=sys.stderr)
        raise


def main() -> None:
    """
    Entry point for CLI command.

    Called by: uv run cleanup-blacklist
    """
    try:
        deleted_count = asyncio.run(cleanup_expired_tokens())

        if deleted_count > 0:
            print(f"\n💡 Tip: Run this command every 1-2 weeks to keep the blacklist table small")
        else:
            print(f"\n✨ No expired tokens to clean up")

        sys.exit(0)

    except KeyboardInterrupt:
        print("\n⚠️  Cleanup interrupted by user", file=sys.stderr)
        sys.exit(130)  # Standard exit code for SIGINT

    except Exception as e:
        logger.error("cleanup_command_failed", error=str(e), exc_info=True)
        print(f"\n❌ Unexpected error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
