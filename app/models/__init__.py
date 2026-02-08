"""
Database models for PostgreSQL.

This package contains all data model definitions for the A2W platform.

Key models:
    - user.py: User with authentication and RBAC
    - aretan_profile.py: Extended profile for Aretan users
    - contractor_profile.py: Extended profile for Contratante users
    - work_experience.py: Work history for Aretans
    - master_tables.py: Admin-managed lookup tables (industries, professions, achievements)
    - item.py: Example CRUD resource (boilerplate reference)

Related files:
    - app/db/postgres.py: Base class and session management
    - app/repositories/: Data access layer
    - alembic/env.py: Import models for migrations
"""
