"""
Database models for PostgreSQL and MongoDB.

This package contains all data model definitions, organized by database type.
Models define the structure and relationships of data stored in the application.

Key components:
    - postgres/: SQLAlchemy models for relational data
        - user.py: User model with authentication and RBAC
        - item.py: Example CRUD resource model
    - mongodb/: Beanie documents for flexible/document data
        - document.py: Example document with flexible schema

Dependencies:
    - sqlalchemy: PostgreSQL ORM
    - beanie: MongoDB ODM
    - app.db: Database connections

Related files:
    - app/db/postgres.py: Base class and session management
    - app/db/mongodb.py: Beanie initialization
    - app/repositories/: Data access layer
    - alembic/env.py: Import models for migrations

Example:
    Import models::

        from app.models.postgres.user import User
        from app.models.postgres.item import Item
        from app.models.mongodb.document import ExampleDocument
"""
