"""
Structured logging configuration using structlog.

Provides application-wide logging with environment-aware output formatting,
automatic context enrichment, and sensitive data censoring.

Key components:
    - configure_logging: Initialize structlog with appropriate processors
    - get_logger: Get a configured logger instance for a module
    - add_app_context: Processor that adds app name, version, environment
    - censor_sensitive_data: Processor that redacts passwords, tokens, etc.

Dependencies:
    - structlog: Structured logging library
    - app.config: Environment and log level settings

Related files:
    - app/config.py: LOG_LEVEL, ENVIRONMENT settings
    - app/main.py: Calls configure_logging() on startup
    - All modules: Use get_logger(__name__) for logging

Common commands:
    - View logs: docker compose logs -f api
    - Change level: Set LOG_LEVEL=DEBUG in .env

Example:
    Using the logger in a module::

        from app.common.logging import get_logger

        logger = get_logger(__name__)

        # Event-based logging with structured data
        logger.info("user_login", user_id=str(user.id), email=user.email)
        logger.warning("rate_limit_exceeded", ip_address=request.client.host)
        logger.error("payment_failed", order_id=str(order.id), error=str(e))

Output formats:
    - Development: Colored console output for readability
    - Production: JSON output for log aggregation (CloudWatch, ELK, etc.)
"""
import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from app.config import settings


def add_app_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add application context to all log entries."""
    event_dict["app"] = settings.APP_NAME
    event_dict["version"] = settings.APP_VERSION
    event_dict["environment"] = settings.ENVIRONMENT
    return event_dict


def censor_sensitive_data(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Censor sensitive data from logs."""
    sensitive_keys = {"password", "token", "secret", "authorization", "api_key"}

    for key in list(event_dict.keys()):
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            event_dict[key] = "***CENSORED***"

    return event_dict


def configure_logging() -> None:
    """Configure structlog and standard logging."""

    # Determine if we should use JSON or console output
    use_json = settings.is_production

    # Shared processors for all log entries
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        add_app_context,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        censor_sensitive_data,
    ]

    if use_json:
        # Production: JSON output for CloudWatch/ELK
        structlog.configure(
            processors=shared_processors + [
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
    else:
        # Development: Pretty console output
        structlog.configure(
            processors=shared_processors + [
                structlog.processors.format_exc_info,
                structlog.dev.ConsoleRenderer(colors=True),
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL),
    )

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)
