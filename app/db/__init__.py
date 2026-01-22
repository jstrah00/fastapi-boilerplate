"""
Database connection and session management.

This package provides database connectivity for both PostgreSQL and MongoDB,
including session factories, connection pooling, and transaction management.

Key components:
    - postgres: SQLAlchemy async engine, sessions, and Base class
    - mongodb: Motor async client and Beanie ODM initialization
    - unit_of_work: Cross-database transaction coordination

Dependencies:
    - sqlalchemy[asyncio]: PostgreSQL ORM
    - asyncpg: PostgreSQL async driver
    - motor: MongoDB async driver
    - beanie: MongoDB ODM

Related files:
    - app/config.py: Database connection settings
    - app/models/: Model definitions for both databases
    - app/main.py: Database initialization on startup

Example:
    Import database utilities::

        from app.db.postgres import get_db, Base
        from app.db.mongodb import get_mongodb_database
        from app.db.unit_of_work import UnitOfWork
"""
