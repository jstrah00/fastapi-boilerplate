"""
Database initialization script.

# =============================================================================
# USAGE: Creates database tables and a default admin user.
#
#   make db-init
#   # or
#   uv run python scripts/init_db.py
#
# CUSTOMIZATION:
# - Change the default admin email and password below
# - Add additional seed data as needed
# =============================================================================
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.postgres import init_db, AsyncSessionLocal
from app.db.mongodb import init_mongodb
from app.models.postgres.user import User
from app.core.security import get_password_hash
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


# =============================================================================
# Configuration - CHANGE THESE VALUES
# =============================================================================

# Default admin credentials - CHANGE IN PRODUCTION!
DEFAULT_ADMIN_EMAIL = "admin@example.com"
DEFAULT_ADMIN_PASSWORD = "admin123"  # Change this!
DEFAULT_ADMIN_FIRST_NAME = "Admin"
DEFAULT_ADMIN_LAST_NAME = "User"


async def create_admin_user() -> None:
    """
    Create a default admin user if it doesn't exist.

    CUSTOMIZATION: Modify this function to create your initial users.
    """
    async with AsyncSessionLocal() as session:
        try:
            from sqlalchemy import select

            # Check if admin exists
            result = await session.execute(
                select(User).where(User.email == DEFAULT_ADMIN_EMAIL)
            )
            existing = result.scalar_one_or_none()

            if existing:
                logger.info("admin_exists", email=DEFAULT_ADMIN_EMAIL)
                print(f"   Admin user already exists: {DEFAULT_ADMIN_EMAIL}")
                return

            # Create admin user with admin role
            admin = User(
                email=DEFAULT_ADMIN_EMAIL,
                first_name=DEFAULT_ADMIN_FIRST_NAME,
                last_name=DEFAULT_ADMIN_LAST_NAME,
                password_hash=get_password_hash(DEFAULT_ADMIN_PASSWORD),
                role="admin",  # Admin role - see app/core/permissions.py
                status="active",
            )

            session.add(admin)
            await session.commit()

            logger.info(
                "admin_created",
                email=DEFAULT_ADMIN_EMAIL,
                message="Default password set - CHANGE THIS!",
            )

            print("\n" + "=" * 60)
            print("  Admin user created successfully!")
            print(f"  Email: {DEFAULT_ADMIN_EMAIL}")
            print(f"  Password: {DEFAULT_ADMIN_PASSWORD}")
            print("  CHANGE THIS PASSWORD IMMEDIATELY!")
            print("=" * 60 + "\n")

        except Exception as e:
            logger.error("admin_creation_failed", error=str(e), exc_info=True)
            await session.rollback()
            raise


async def main() -> None:
    """Initialize database and create seed data."""
    try:
        print("\n  Initializing database...\n")

        # Initialize PostgreSQL
        print("  Creating PostgreSQL tables...")
        await init_db()
        print("  PostgreSQL tables created\n")

        # Initialize MongoDB
        print("  Initializing MongoDB...")
        await init_mongodb()
        print("  MongoDB initialized\n")

        # Create admin user
        print("  Creating admin user...")
        await create_admin_user()

        print("\n  Database initialization complete!\n")

    except Exception as e:
        logger.error("initialization_failed", error=str(e), exc_info=True)
        print(f"\n  Initialization failed: {str(e)}\n")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
