"""
FastAPI Boilerplate - Main Application.

# =============================================================================
# MAIN: Application entry point with lifespan management.
# =============================================================================
"""
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.common.logging import configure_logging, get_logger
from app.common.exceptions import AppException
from app.db.postgres import init_db as init_postgres, close_db as close_postgres
from app.db.mongodb import init_mongodb, close_mongodb
from app.api.v1.router import api_router
from app.api.handlers import (
    app_exception_handler,
    validation_exception_handler,
    general_exception_handler,
)

# Configure logging first
configure_logging()
logger = get_logger(__name__)


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
        # Initialize PostgreSQL
        # NOTE: In development, this creates tables. In production, use Alembic migrations.
        if settings.is_development:
            await init_postgres()

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

# =============================================================================
# Middleware
# =============================================================================
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
