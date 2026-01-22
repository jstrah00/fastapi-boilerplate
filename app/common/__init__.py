"""
Shared utilities and cross-cutting concerns.

This package provides common functionality used throughout the application,
including security, logging, permissions, exceptions, and alerts.

Key components:
    - logging: Structured logging with structlog
    - security: JWT tokens and password hashing
    - permissions: Role-based access control (RBAC)
    - exceptions: Application exception hierarchy
    - alerts: Telegram notifications for critical errors

Dependencies:
    - structlog: Structured logging
    - python-jose: JWT handling
    - passlib: Password hashing
    - httpx: Async HTTP for alerts

Related files:
    - app/config.py: Settings used by these modules
    - app/api/deps.py: Uses security for authentication
    - app/api/handlers.py: Uses exceptions and alerts

Example:
    Import common utilities::

        from app.common.logging import get_logger
        from app.common.security import get_password_hash, verify_password
        from app.common.permissions import Permission, require_permissions
        from app.common.exceptions import NotFoundError, ValidationError
        from app.common.alerts import telegram_alert
"""
