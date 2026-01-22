"""
Exception handlers for FastAPI application.

# =============================================================================
# EXCEPTION HANDLERS: Global error handling for the API.
# Converts exceptions to appropriate HTTP responses.
# =============================================================================
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.common.logging import get_logger
from app.common.exceptions import (
    AppException,
    should_send_alert,
    CriticalError,
)
from app.common.alerts import telegram_alert

logger = get_logger(__name__)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    Handle custom application exceptions.

    Logs all errors and sends Telegram alerts for critical ones.
    """
    exception_name = exc.__class__.__name__

    # Log always
    logger.error(
        "app_exception",
        exception_type=exception_name,
        message=exc.message,
        details=exc.details,
        path=request.url.path,
        method=request.method,
    )

    # Send alert if needed
    if should_send_alert(exc):
        alert_level = "CRITICAL" if isinstance(exc, CriticalError) else "ERROR"

        await telegram_alert.send_alert(
            message=f"Error in API: {exception_name}",
            level=alert_level,
            extra_data={
                "exception": exception_name,
                "message": exc.message,
                "path": request.url.path,
                "method": request.method,
                "details": str(exc.details)[:200],
            },
        )

    # Map exception types to HTTP status codes
    from app.common.exceptions import (
        AuthenticationError,
        AuthorizationError,
        NotFoundError,
        AlreadyExistsError,
        ValidationError,
        DatabaseError,
        ExternalServiceError,
    )

    status_map = {
        AuthenticationError: status.HTTP_401_UNAUTHORIZED,
        AuthorizationError: status.HTTP_403_FORBIDDEN,
        NotFoundError: status.HTTP_404_NOT_FOUND,
        AlreadyExistsError: status.HTTP_409_CONFLICT,
        ValidationError: status.HTTP_400_BAD_REQUEST,
        DatabaseError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        ExternalServiceError: status.HTTP_503_SERVICE_UNAVAILABLE,
    }

    # Find the status code by exception type
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    for exc_class, exc_status in status_map.items():
        if isinstance(exc, exc_class):
            status_code = exc_status
            break

    return JSONResponse(
        status_code=status_code,
        content={
            "error": exception_name,
            "message": exc.message,
            "details": exc.details,
        },
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Handle Pydantic validation errors.

    These are client errors (invalid input), so no alerts needed.
    """
    logger.warning(
        "validation_error",
        errors=exc.errors(),
        body=exc.body,
        path=request.url.path,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "message": "Request validation failed",
            "details": exc.errors(),
        },
    )


async def general_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Handle unexpected exceptions (bugs).

    ALWAYS sends alert - these should never happen in production.
    """
    exception_name = exc.__class__.__name__

    logger.error(
        "unexpected_exception",
        exception_type=exception_name,
        error=str(exc),
        path=request.url.path,
        method=request.method,
        exc_info=True,
    )

    # Always alert for unhandled exceptions (they are bugs)
    await telegram_alert.send_alert(
        message="Unhandled exception in API",
        level="CRITICAL",
        extra_data={
            "exception": exception_name,
            "error": str(exc)[:300],
            "path": request.url.path,
            "method": request.method,
        },
    )

    if settings.is_production:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "InternalServerError",
                "message": "An unexpected error occurred",
            },
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": exception_name,
                "message": str(exc),
            },
        )
