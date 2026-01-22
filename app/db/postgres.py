"""
PostgreSQL database configuration using SQLAlchemy with async support.

Provides async database engine, session factory, and connection management
for PostgreSQL using SQLAlchemy 2.0+ with asyncpg driver.

Key components:
    - Base: Declarative base class for all SQLAlchemy models
    - engine: Async database engine with connection pooling
    - AsyncSessionLocal: Session factory for creating database sessions
    - get_db: FastAPI dependency for injecting database sessions

Dependencies:
    - sqlalchemy[asyncio]: ORM and async support
    - asyncpg: PostgreSQL async driver
    - app.config: Database connection settings

Related files:
    - app/config.py: Database URL and pool settings
    - app/models/postgres/: SQLAlchemy model definitions
    - app/repositories/: Data access layer using sessions
    - alembic/env.py: Migration environment

Common commands:
    - Migrate: uv run alembic upgrade head
    - Create migration: uv run alembic revision --autogenerate -m "description"
    - Downgrade: uv run alembic downgrade -1

Example:
    Using in a FastAPI endpoint::

        from fastapi import Depends
        from sqlalchemy.ext.asyncio import AsyncSession
        from app.db.postgres import get_db

        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()

Note:
    If your project only needs MongoDB, you can safely delete this file,
    the app/models/postgres/ folder, and related dependencies.
"""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.config import settings
from app.common.logging import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    """
    Base class for SQLAlchemy models.

    All PostgreSQL models should inherit from this class.
    """

    pass


# Create async engine
engine = create_async_engine(
    settings.postgres_url,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    pool_size=settings.POSTGRES_POOL_SIZE,
    max_overflow=settings.POSTGRES_MAX_OVERFLOW,
    pool_pre_ping=True,  # Verify connections before using them
    # Use NullPool for testing to avoid connection issues
    poolclass=NullPool if settings.ENVIRONMENT == "test" else None,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for getting async database sessions.

    Yields:
        AsyncSession: Database session

    Example:
        ```python
        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
        ```
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database by creating all tables.

    NOTE: In production, use Alembic migrations instead of this function.
    This is only for development to quickly create tables.
    """
    try:
        async with engine.begin() as conn:
            # Import all models here to ensure they're registered with Base
            from app.models.postgres import user, item  # noqa: F401

            # Create all tables
            await conn.run_sync(Base.metadata.create_all)

        logger.info("postgres_initialized", message="PostgreSQL tables created")
    except Exception as e:
        logger.error("postgres_init_failed", error=str(e))
        raise


async def close_db() -> None:
    """Close database connections."""
    try:
        await engine.dispose()
        logger.info("postgres_closed", message="PostgreSQL connections closed")
    except Exception as e:
        logger.error("postgres_close_failed", error=str(e))
        raise
