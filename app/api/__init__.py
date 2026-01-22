"""
API layer containing endpoints, dependencies, and exception handlers.

This package provides the HTTP interface for the application, including
versioned API endpoints, dependency injection, and error handling.

Key components:
    - deps.py: Dependency injection for services and authentication
    - handlers.py: Global exception handlers
    - v1/: Version 1 API endpoints

Dependencies:
    - fastapi: Web framework
    - app.services: Business logic layer
    - app.schemas: Request/response DTOs

Related files:
    - app/main.py: Mounts the API router
    - app/config.py: API_V1_PREFIX setting

Example:
    Import API components::

        from app.api.deps import CurrentUser, UserSvc
        from app.api.handlers import app_exception_handler
        from app.api.v1.router import api_router
"""
