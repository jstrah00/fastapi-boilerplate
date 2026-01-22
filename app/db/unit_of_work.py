"""
Unit of Work pattern for coordinating transactions across PostgreSQL and MongoDB.

Provides a context manager that manages transactions across both databases,
ensuring atomic operations that either fully commit or fully rollback.

Key components:
    - UnitOfWork: Context manager for cross-database transactions
    - postgres_session: SQLAlchemy async session for PostgreSQL
    - mongo_session: Motor session for MongoDB transactions
    - commit: Commit both database transactions
    - rollback: Rollback both database transactions

Dependencies:
    - sqlalchemy.ext.asyncio: Async SQLAlchemy sessions
    - motor.motor_asyncio: Async MongoDB sessions
    - app.db.postgres: PostgreSQL session factory
    - app.db.mongodb: MongoDB client

Related files:
    - app/db/postgres.py: PostgreSQL session management
    - app/db/mongodb.py: MongoDB client management
    - app/services/: Services that may use UnitOfWork

Common commands:
    - Test: uv run pytest tests/ -k "unit_of_work"

Example:
    Cross-database atomic operation::

        from app.db.unit_of_work import UnitOfWork

        async with UnitOfWork() as uow:
            # PostgreSQL operation
            user = User(email="test@example.com")
            uow.postgres_session.add(user)

            # MongoDB operation
            await uow.mongo_db["documents"].insert_one({
                "user_id": str(user.id),
                "data": {"key": "value"}
            })

            # Both commit together or both rollback
            await uow.commit()

Note:
    Only necessary if using BOTH databases and need coordinated transactions.
    If using only one database, use regular sessions directly in services.
"""
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClientSession
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.logging import get_logger
from app.db.mongodb import get_mongodb_client
from app.db.postgres import AsyncSessionLocal

logger = get_logger(__name__)


class UnitOfWork:
    """
    Unit of Work for managing transactions across PostgreSQL and MongoDB.

    # EXAMPLE USAGE:
    ```python
    async with UnitOfWork() as uow:
        # PostgreSQL operations
        user = User(email="test@example.com")
        uow.postgres_session.add(user)

        # MongoDB operations
        doc = await uow.mongo_db["documents"].insert_one({...})

        # Commit both databases
        await uow.commit()
    # Auto-rollback if any exception occurs
    ```

    # NOTE: If only using one database, you don't need this class.
    # Use regular sessions directly instead.
    """

    def __init__(self) -> None:
        self.postgres_session: AsyncSession | None = None
        self.mongo_session: AsyncIOMotorClientSession | None = None
        self._committed = False
        self._rolled_back = False

    async def __aenter__(self) -> "UnitOfWork":
        """Initialize both database sessions."""
        try:
            # Start PostgreSQL session
            self.postgres_session = AsyncSessionLocal()

            # Start MongoDB session (for transactions)
            mongo_client = get_mongodb_client()
            self.mongo_session = await mongo_client.start_session()
            self.mongo_session.start_transaction()

            logger.debug("uow_started", message="Unit of Work started")
            return self

        except Exception as e:
            logger.error("uow_start_failed", error=str(e))
            await self._cleanup()
            raise

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """
        Clean up sessions on exit.

        If an exception occurred and commit wasn't called, rollback.
        """
        try:
            if exc_type is not None:
                # Exception occurred, rollback if not already done
                if not self._rolled_back and not self._committed:
                    await self.rollback()
            else:
                # No exception, commit if not already done
                if not self._committed and not self._rolled_back:
                    await self.commit()
        finally:
            await self._cleanup()

    async def commit(self) -> None:
        """
        Commit both PostgreSQL and MongoDB transactions.

        Raises:
            Exception: If commit fails in either database
        """
        if self._committed:
            logger.warning("uow_already_committed", message="Unit of Work already committed")
            return

        if self._rolled_back:
            raise RuntimeError("Cannot commit after rollback")

        try:
            # Commit PostgreSQL first (as it's more likely to fail)
            if self.postgres_session:
                await self.postgres_session.commit()
                logger.debug("uow_postgres_committed")

            # Commit MongoDB
            if self.mongo_session:
                await self.mongo_session.commit_transaction()
                logger.debug("uow_mongo_committed")

            self._committed = True
            logger.info("uow_committed", message="Unit of Work committed successfully")

        except Exception as e:
            logger.error("uow_commit_failed", error=str(e))
            # If commit fails, try to rollback
            await self.rollback()
            raise

    async def rollback(self) -> None:
        """Rollback both PostgreSQL and MongoDB transactions."""
        if self._rolled_back:
            logger.warning("uow_already_rolled_back", message="Unit of Work already rolled back")
            return

        errors = []

        # Rollback PostgreSQL
        if self.postgres_session:
            try:
                await self.postgres_session.rollback()
                logger.debug("uow_postgres_rolled_back")
            except Exception as e:
                logger.error("uow_postgres_rollback_failed", error=str(e))
                errors.append(f"PostgreSQL rollback: {str(e)}")

        # Rollback MongoDB
        if self.mongo_session:
            try:
                await self.mongo_session.abort_transaction()
                logger.debug("uow_mongo_rolled_back")
            except Exception as e:
                logger.error("uow_mongo_rollback_failed", error=str(e))
                errors.append(f"MongoDB rollback: {str(e)}")

        self._rolled_back = True

        if errors:
            error_msg = "; ".join(errors)
            logger.error("uow_rollback_errors", errors=error_msg)
            raise Exception(f"Rollback errors: {error_msg}")

        logger.info("uow_rolled_back", message="Unit of Work rolled back successfully")

    async def _cleanup(self) -> None:
        """Clean up database sessions."""
        # Close MongoDB session
        if self.mongo_session:
            try:
                await self.mongo_session.end_session()
            except Exception as e:
                logger.error("uow_mongo_cleanup_failed", error=str(e))

        # Close PostgreSQL session
        if self.postgres_session:
            try:
                await self.postgres_session.close()
            except Exception as e:
                logger.error("uow_postgres_cleanup_failed", error=str(e))

        logger.debug("uow_cleaned_up", message="Unit of Work cleaned up")

    @property
    def mongo_db(self) -> Any:
        """
        Get MongoDB database with session context.

        Returns:
            MongoDB database that will use the active transaction session
        """
        from app.db.mongodb import get_mongodb_database

        return get_mongodb_database()
