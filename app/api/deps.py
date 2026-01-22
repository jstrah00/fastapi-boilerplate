"""
FastAPI dependencies for dependency injection.

# =============================================================================
# DEPENDENCIES: Dependency injection for services, repositories, and auth.
# This is where you wire up your application components.
# =============================================================================
"""
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.repositories.user_repo import UserRepository
from app.repositories.item_repo import ItemRepository
from app.services.user_service import UserService
from app.services.auth_service import AuthService
from app.services.item_service import ItemService
from app.models.postgres.user import User
from app.common.security import decode_token
from app.common.logging import get_logger

logger = get_logger(__name__)

# Bearer token authentication
security_scheme = HTTPBearer()


# =============================================================================
# Repository Dependencies
# =============================================================================

async def get_user_repository(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> UserRepository:
    """Get user repository instance."""
    return UserRepository(db)


async def get_item_repository(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> ItemRepository:
    """Get item repository instance."""
    return ItemRepository(db)


# =============================================================================
# Service Dependencies
# =============================================================================

async def get_user_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)]
) -> UserService:
    """Get user service instance."""
    return UserService(user_repo)


async def get_auth_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)]
) -> AuthService:
    """Get auth service instance."""
    return AuthService(user_repo)


async def get_item_service(
    item_repo: Annotated[ItemRepository, Depends(get_item_repository)]
) -> ItemService:
    """Get item service instance."""
    return ItemService(item_repo)


# =============================================================================
# Authentication Dependencies
# =============================================================================

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security_scheme)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        token: JWT access token
        user_repo: User repository

    Returns:
        Current user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Decode token
    token = credentials.credentials
    payload = decode_token(token)
    if payload is None:
        logger.warning("invalid_token", message="Token decode failed")
        raise credentials_exception

    # Check token type
    if payload.get("type") != "access":
        logger.warning("invalid_token_type", token_type=payload.get("type"))
        raise credentials_exception

    # Get user ID from token
    user_id_str: str | None = payload.get("sub")
    if user_id_str is None:
        logger.warning("invalid_token_payload", message="Missing user ID")
        raise credentials_exception

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        logger.warning("invalid_user_id", user_id=user_id_str)
        raise credentials_exception

    # Get user from database
    user = await user_repo.get(user_id)
    if user is None:
        logger.warning("user_not_found_from_token", user_id=user_id_str)
        raise credentials_exception

    logger.debug("user_authenticated", user_id=user_id_str, email=user.email)
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Get current active user.

    Args:
        current_user: Current user from token

    Returns:
        Active user

    Raises:
        HTTPException: If user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not active",
        )
    return current_user


async def get_current_admin(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> User:
    """
    Get current admin user.

    Args:
        current_user: Current active user

    Returns:
        Admin user

    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.is_admin:
        logger.warning(
            "admin_required",
            user_id=str(current_user.id),
            email=current_user.email,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


# =============================================================================
# Type Aliases for cleaner code
# =============================================================================

# Auth
CurrentUser = Annotated[User, Depends(get_current_active_user)]
CurrentAdmin = Annotated[User, Depends(get_current_admin)]

# Repositories
UserRepo = Annotated[UserRepository, Depends(get_user_repository)]
ItemRepo = Annotated[ItemRepository, Depends(get_item_repository)]

# Services
UserSvc = Annotated[UserService, Depends(get_user_service)]
AuthSvc = Annotated[AuthService, Depends(get_auth_service)]
ItemSvc = Annotated[ItemService, Depends(get_item_service)]
