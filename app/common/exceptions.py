"""
Custom exception classes for the application.

Provides a hierarchical exception system that separates expected business errors
from critical system errors, enabling appropriate handling and alerting.

Key components:
    - AppException: Base exception for all application errors
    - ExpectedError: Base for business logic errors (no alerts sent)
        - AuthenticationError: Invalid credentials, expired tokens
        - AuthorizationError: Insufficient permissions
        - NotFoundError: Resource not found
        - AlreadyExistsError: Duplicate resource (e.g., email already taken)
        - ValidationError: Business rule violations
    - CriticalError: Base for system errors (alerts sent)
        - DatabaseError: Database operation failures
        - ExternalServiceError: Third-party API failures
    - should_send_alert: Determine if exception should trigger alert

Dependencies:
    - None (standalone module)

Related files:
    - app/api/handlers.py: Exception handlers that convert these to HTTP responses
    - app/common/alerts.py: Telegram alerts for critical errors
    - app/services/: Services raise these exceptions
    - app/api/v1/: Routers catch and convert to HTTPException

Common commands:
    - Test: uv run pytest tests/ -k "exception"

Example:
    Raising exceptions in services::

        from app.common.exceptions import NotFoundError, AlreadyExistsError

        async def get_user(self, user_id: UUID) -> User:
            user = await self.repo.get(user_id)
            if not user:
                raise NotFoundError(
                    message="User not found",
                    details={"user_id": str(user_id)}
                )
            return user

        async def create_user(self, email: str) -> User:
            if await self.repo.get_by_email(email):
                raise AlreadyExistsError(
                    message="User with this email already exists",
                    details={"email": email}
                )
            ...
"""
from typing import Any


class AppException(Exception):
    """
    Base exception for all application errors.

    All custom exceptions should inherit from this class.
    """

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r})"


# =============================================================================
# Expected Errors (Business Logic) - Don't send alerts
# =============================================================================

class ExpectedError(AppException):
    """
    Base class for expected/business logic errors.

    These errors are part of normal operation (invalid input, not found, etc.)
    and should NOT trigger system alerts.
    """

    pass


class AuthenticationError(ExpectedError):
    """User authentication failed (invalid credentials, expired token, etc.)."""

    pass


class AuthorizationError(ExpectedError):
    """User is not authorized to perform the action."""

    pass


class NotFoundError(ExpectedError):
    """Requested resource was not found."""

    pass


class AlreadyExistsError(ExpectedError):
    """Resource already exists (duplicate email, etc.)."""

    pass


class ValidationError(ExpectedError):
    """Input validation failed or business rule violation."""

    pass


# =============================================================================
# Critical Errors (System) - Send alerts
# =============================================================================

class CriticalError(AppException):
    """
    Base class for critical/system errors.

    These errors indicate system problems and SHOULD trigger alerts.
    """

    pass


class DatabaseError(CriticalError):
    """Database operation failed."""

    pass


class ExternalServiceError(CriticalError):
    """External service (API, email, etc.) failed."""

    pass


# =============================================================================
# Helper Functions
# =============================================================================

def should_send_alert(exception: AppException) -> bool:
    """
    Determine if an alert should be sent for this exception.

    Args:
        exception: The exception to check

    Returns:
        True if alert should be sent, False otherwise
    """
    # Critical errors always send alerts
    if isinstance(exception, CriticalError):
        return True

    # Expected errors don't send alerts by default
    if isinstance(exception, ExpectedError):
        return False

    # Unknown AppException types send alerts (to be safe)
    return True
