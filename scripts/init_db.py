"""
Database initialization script for A2W platform.

Creates tables, default admin user, and seeds master data.

Usage:
    uv run python scripts/init_db.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.db.postgres import init_db, AsyncSessionLocal
from app.models.postgres.user import User
from app.models.postgres.master_tables import (
    MasterIndustry,
    MasterProfession,
    MasterSportAchievement,
)
from app.common.security import get_password_hash
from app.common.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

# Default admin credentials
DEFAULT_ADMIN_EMAIL = "admin@example.com"
DEFAULT_ADMIN_PASSWORD = "Admin123!"
DEFAULT_ADMIN_FIRST_NAME = "Admin"
DEFAULT_ADMIN_LAST_NAME = "A2W"

# Master data seeds
SPORT_ACHIEVEMENTS = [
    ("Olímpico", 1),
    ("Mundialista", 2),
    ("Panamericano", 3),
    ("Selección nacional", 4),
    ("Club profesional", 5),
    ("Primera división", 6),
]

INDUSTRIES = [
    ("Tecnología", 1),
    ("Finanzas", 2),
    ("Salud", 3),
    ("Educación", 4),
    ("Marketing", 5),
    ("Consultoría", 6),
    ("Construcción", 7),
    ("Industria", 8),
    ("Comercio", 9),
    ("Deporte", 10),
    ("Medios y comunicación", 11),
    ("Legal", 12),
    ("Otros", 99),
]

PROFESSIONS = [
    ("Ingeniero/a", 1),
    ("Abogado/a", 2),
    ("Contador/a", 3),
    ("Médico/a", 4),
    ("Arquitecto/a", 5),
    ("Docente", 6),
    ("Administrador/a", 7),
    ("Comunicador/a", 8),
    ("Diseñador/a", 9),
    ("Desarrollador/a", 10),
    ("Analista", 11),
    ("Consultor/a", 12),
    ("Martillero/a", 13),
    ("Comerciante", 14),
    ("Otros", 99),
]


async def create_admin_user() -> None:
    """Create a default admin user if it doesn't exist."""
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                select(User).where(User.email == DEFAULT_ADMIN_EMAIL)
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"   Admin user already exists: {DEFAULT_ADMIN_EMAIL}")
                return

            admin = User(
                email=DEFAULT_ADMIN_EMAIL,
                first_name=DEFAULT_ADMIN_FIRST_NAME,
                last_name=DEFAULT_ADMIN_LAST_NAME,
                password_hash=get_password_hash(DEFAULT_ADMIN_PASSWORD),
                role="admin",
                status="active",
            )

            session.add(admin)
            await session.commit()

            print(f"   Admin created: {DEFAULT_ADMIN_EMAIL} / {DEFAULT_ADMIN_PASSWORD}")

        except Exception as e:
            logger.error("admin_creation_failed", error=str(e), exc_info=True)
            await session.rollback()
            raise


async def seed_master_data() -> None:
    """Seed master list tables with initial data."""
    async with AsyncSessionLocal() as session:
        try:
            # Sport achievements
            result = await session.execute(select(MasterSportAchievement).limit(1))
            if not result.scalar_one_or_none():
                for name, order in SPORT_ACHIEVEMENTS:
                    session.add(MasterSportAchievement(
                        name=name, display_order=order
                    ))
                print(f"   Seeded {len(SPORT_ACHIEVEMENTS)} sport achievements")
            else:
                print("   Sport achievements already seeded")

            # Industries
            result = await session.execute(select(MasterIndustry).limit(1))
            if not result.scalar_one_or_none():
                for name, order in INDUSTRIES:
                    session.add(MasterIndustry(name=name, display_order=order))
                print(f"   Seeded {len(INDUSTRIES)} industries")
            else:
                print("   Industries already seeded")

            # Professions
            result = await session.execute(select(MasterProfession).limit(1))
            if not result.scalar_one_or_none():
                for name, order in PROFESSIONS:
                    session.add(MasterProfession(name=name, display_order=order))
                print(f"   Seeded {len(PROFESSIONS)} professions")
            else:
                print("   Professions already seeded")

            await session.commit()

        except Exception as e:
            logger.error("seed_failed", error=str(e), exc_info=True)
            await session.rollback()
            raise


async def main() -> None:
    """Initialize database and create seed data."""
    try:
        print("\n  Initializing A2W database...\n")

        print("  Creating PostgreSQL tables...")
        await init_db()
        print("  PostgreSQL tables created\n")

        print("  Creating admin user...")
        await create_admin_user()

        print("\n  Seeding master data...")
        await seed_master_data()

        print("\n  Database initialization complete!\n")

    except Exception as e:
        logger.error("initialization_failed", error=str(e), exc_info=True)
        print(f"\n  Initialization failed: {str(e)}\n")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
