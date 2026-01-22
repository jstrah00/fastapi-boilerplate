"""
Data access repositories implementing the Repository Pattern.

Provides an abstraction layer between business logic and database operations,
with a generic base class and model-specific implementations.

Key components:
    - BaseRepository: Generic CRUD operations for any SQLAlchemy model
    - UserRepository: User-specific queries (by email, active users, admins)
    - ItemRepository: Item-specific queries (by owner)

Dependencies:
    - sqlalchemy: ORM operations
    - app.models.postgres: SQLAlchemy models

Related files:
    - app/db/postgres.py: Database session management
    - app/services/: Business logic layer that uses repositories
    - app/api/deps.py: Dependency injection setup

Common commands:
    - Test: uv run pytest tests/ -k "repository"

Example:
    Import repositories::

        from app.repositories import UserRepository, ItemRepository

    Creating a new repository::

        from app.repositories.base import BaseRepository
        from app.models.postgres.product import Product

        class ProductRepository(BaseRepository[Product]):
            def __init__(self, db: AsyncSession):
                super().__init__(Product, db)

            # Add custom query methods here

Benefits of Repository Pattern:
    - Separates data access from business logic
    - Makes services easier to test with mock repositories
    - Centralizes query logic for reuse
    - Provides consistent interface for all models
"""
from app.repositories.base import BaseRepository
from app.repositories.user_repo import UserRepository
from app.repositories.item_repo import ItemRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "ItemRepository",
]
