"""
FastAPI Boilerplate - Main Application Entry Point.

Initializes the FastAPI application with middleware, exception handlers,
database connections, and API routers. Manages application lifecycle.

Key components:
    - app: FastAPI application instance
    - lifespan: Async context manager for startup/shutdown
    - Middleware: CORS configuration
    - Exception handlers: App, validation, and general error handling
    - Health check: /health endpoint for monitoring

Dependencies:
    - fastapi: Web framework
    - app.config: Application settings
    - app.db: Database initialization
    - app.api: Routers and handlers

Related files:
    - app/config.py: Settings loaded from environment
    - app/db/postgres.py: PostgreSQL initialization
    - app/db/mongodb.py: MongoDB initialization
    - app/api/v1/router.py: API routes
    - app/api/handlers.py: Exception handlers

Common commands:
    - Development: uv run dev
    - Production: uvicorn app.main:app --host 0.0.0.0 --port 8000
    - Docker: docker compose up -d

Example:
    Running the application::

        # Development with auto-reload
        uv run dev

        # Or directly with uvicorn
        uvicorn app.main:app --reload

        # Production
        uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

    Accessing the API::

        # Health check
        curl http://localhost:8000/health

        # API documentation
        open http://localhost:8000/docs

Lifecycle events:
    - Startup: Initialize PostgreSQL, MongoDB, configure logging
    - Shutdown: Close database connections gracefully
"""

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.api.handlers import (
    app_exception_handler,
    general_exception_handler,
    validation_exception_handler,
)
from app.api.v1.router import api_router
from app.common.exceptions import AppException
from app.common.logging import configure_logging, get_logger
from app.config import settings
from app.db.mongodb import close_mongodb, init_mongodb
from app.db.postgres import close_db as close_postgres

# Configure logging first
configure_logging()
logger = get_logger(__name__)

# Global rate limiter — per-IP defaults; per-endpoint @limiter.limit overrides apply on top.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["120/minute", "1000/hour"],
)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Bind a per-request UUID to structlog's contextvars and the X-Request-ID header.

    Every log line emitted while handling the request will carry `request_id`,
    so traces can be reassembled across services. Clients may pass their own
    X-Request-ID; otherwise we generate one.
    """

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        try:
            response: Response = await call_next(request)
        finally:
            structlog.contextvars.clear_contextvars()
        response.headers["X-Request-ID"] = request_id
        return response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Application lifespan handler for startup and shutdown events.

    This is where you initialize and cleanup resources like database connections.
    """
    # ==========================================================================
    # STARTUP
    # ==========================================================================
    logger.info(
        "application_startup",
        app_name=settings.APP_NAME,
        environment=settings.ENVIRONMENT,
        debug=settings.DEBUG,
    )

    try:
        # PostgreSQL schema is owned by Alembic in every environment, including
        # dev. Run `uv run alembic upgrade head` before starting the app. The
        # previous init_postgres() call here bypassed migrations and caused
        # drift between dev (auto-created tables) and prod (Alembic-managed).

        # Initialize MongoDB
        # NOTE: If not using MongoDB, comment out or remove this line
        await init_mongodb()

        logger.info("databases_initialized", message="All databases ready")

    except Exception as e:
        logger.error("startup_failed", error=str(e), exc_info=True)
        raise

    yield  # Application runs here

    # ==========================================================================
    # SHUTDOWN
    # ==========================================================================
    logger.info("application_shutdown", message="Shutting down gracefully")

    try:
        await close_postgres()
        await close_mongodb()
        logger.info("databases_closed", message="All database connections closed")

    except Exception as e:
        logger.error("shutdown_error", error=str(e), exc_info=True)


# =============================================================================
# Create FastAPI Application
# =============================================================================
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="FastAPI Boilerplate with PostgreSQL + MongoDB support",
    docs_url="/docs" if settings.DEBUG else None,  # Disable docs in production
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Register rate limiter — SlowAPIMiddleware enforces default_limits app-wide;
# per-endpoint @limiter.limit decorators still apply on top.
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# =============================================================================
# Middleware (order matters: outermost runs first on requests, last on responses)
# =============================================================================
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

# =============================================================================
# Exception Handlers
# =============================================================================
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(Exception, general_exception_handler)


# =============================================================================
# Health Check Endpoint
# =============================================================================
@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint for load balancers and monitoring."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


# =============================================================================
# Include API Routers
# =============================================================================
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# =============================================================================
# Run with Uvicorn (for development)
# =============================================================================
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
