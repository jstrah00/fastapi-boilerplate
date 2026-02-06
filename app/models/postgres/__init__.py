"""
SQLAlchemy models for PostgreSQL.

Contains all relational data models using SQLAlchemy ORM with async support.
All models inherit from Base defined in app.db.postgres.

Key components:
    - User: User model with authentication and RBAC
    - Item: Example CRUD resource model
    - RefreshTokenBlacklist: Blacklist for used/revoked refresh tokens

Dependencies:
    - sqlalchemy: ORM framework
    - app.db.postgres: Base class

Related files:
    - alembic/env.py: Models must be imported here for migrations
    - app/repositories/: Data access layer

Common commands:
    - Create migration: uv run alembic revision --autogenerate -m "description"
    - Apply migration: uv run alembic upgrade head

Example:
    Import models::

        from app.models.postgres import User, Item, RefreshTokenBlacklist
        # or
        from app.models.postgres.user import User

Note:
    When creating new models, import them in alembic/env.py
    for autogenerate to detect schema changes.
"""
from app.models.postgres.user import User
from app.models.postgres.item import Item
from app.models.postgres.refresh_token_blacklist import RefreshTokenBlacklist

__all__ = [
    "User",
    "Item",
    "RefreshTokenBlacklist",
]
