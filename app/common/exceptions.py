"""
Custom exception classes for the application.

# =============================================================================
# EXCEPTIONS: Application-specific exception hierarchy.
#
# Two main categories:
# 1. ExpectedError - Business logic errors (don't send alerts)
# 2. CriticalError - System errors (send alerts)
# =============================================================================
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
