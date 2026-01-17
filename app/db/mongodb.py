"""
MongoDB database configuration using Motor (async) and Beanie ODM.

# =============================================================================
# MONGODB CONFIGURATION
#
# NOTE: If your project only needs PostgreSQL, you can safely delete:
# - This file (app/db/mongodb.py)
# - The app/models/mongodb/ folder
# - MongoDB dependencies from pyproject.toml (motor, beanie, pymongo)
# - MongoDB service from docker-compose.yml
# - MongoDB initialization from app/main.py
# =============================================================================
"""
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Global MongoDB client and database
mongodb_client: AsyncIOMotorClient | None = None
mongodb_db: AsyncIOMotorDatabase | None = None


def get_mongodb_client() -> AsyncIOMotorClient:
    """
    Get MongoDB client instance.

    Returns:
        Motor AsyncIOMotorClient instance

    Raises:
        RuntimeError: If MongoDB is not initialized
    """
    if mongodb_client is None:
        raise RuntimeError("MongoDB client not initialized. Call init_mongodb() first.")
    return mongodb_client


def get_mongodb_database() -> AsyncIOMotorDatabase:
    """
    Get MongoDB database instance.

    Returns:
        Motor AsyncIOMotorDatabase instance

    Raises:
        RuntimeError: If MongoDB is not initialized
    """
    if mongodb_db is None:
        raise RuntimeError("MongoDB database not initialized. Call init_mongodb() first.")
    return mongodb_db


async def init_mongodb() -> None:
    """
    Initialize MongoDB connection and Beanie ODM.

    This should be called on application startup.
    """
    global mongodb_client, mongodb_db

    try:
        # Create Motor client
        mongodb_client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            minPoolSize=settings.MONGODB_MIN_POOL_SIZE,
            maxPoolSize=settings.MONGODB_MAX_POOL_SIZE,
        )

        # Get database
        mongodb_db = mongodb_client[settings.MONGODB_DB]

        # Ping to verify connection
        await mongodb_client.admin.command("ping")

        # Import document models
        from app.models.mongodb.document import ExampleDocument

        # Initialize Beanie with document models
        # NOTE: Add your document models to this list
        await init_beanie(
            database=mongodb_db,
            document_models=[ExampleDocument],
        )

        logger.info(
            "mongodb_initialized",
            message="MongoDB connection established",
            database=settings.MONGODB_DB,
        )
    except Exception as e:
        logger.error("mongodb_init_failed", error=str(e))
        raise


async def close_mongodb() -> None:
    """
    Close MongoDB connections.

    This should be called on application shutdown.
    """
    global mongodb_client, mongodb_db

    try:
        if mongodb_client:
            mongodb_client.close()
            mongodb_client = None
            mongodb_db = None
            logger.info("mongodb_closed", message="MongoDB connections closed")
    except Exception as e:
        logger.error("mongodb_close_failed", error=str(e))
        raise


async def check_mongodb_health() -> bool:
    """
    Check MongoDB connection health.

    Returns:
        True if healthy, False otherwise
    """
    try:
        client = get_mongodb_client()
        await client.admin.command("ping")
        return True
    except Exception as e:
        logger.error("mongodb_health_check_failed", error=str(e))
        return False
