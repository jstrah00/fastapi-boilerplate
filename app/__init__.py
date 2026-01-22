"""
FastAPI Boilerplate Application Package.

A production-ready FastAPI boilerplate with PostgreSQL + MongoDB support,
JWT authentication, role-based access control, and layered architecture.

Key components:
    - main.py: Application entry point and lifecycle management
    - config.py: Centralized configuration with environment variables
    - api/: HTTP endpoints and request handling
    - services/: Business logic layer
    - repositories/: Data access layer
    - models/: Database models (PostgreSQL + MongoDB)
    - schemas/: Pydantic request/response DTOs
    - common/: Shared utilities (security, logging, permissions, etc.)
    - db/: Database connections and session management

Architecture:
    API Layer (routers) -> Service Layer -> Repository Layer -> Models
                                                              |
                                            Schemas (DTOs) <--+

Dependencies:
    - fastapi: Web framework
    - sqlalchemy: PostgreSQL ORM
    - beanie: MongoDB ODM
    - pydantic: Data validation

Common commands:
    - Run: uv run dev
    - Test: uv run test
    - Lint: uv run ruff check app tests
    - Type check: uv run mypy app

Example:
    Import the FastAPI app::

        from app.main import app

    Run with uvicorn::

        uvicorn app.main:app --reload
"""
