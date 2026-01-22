"""
Authentication API endpoints.

Provides endpoints for user authentication including login with email/password,
token refresh, and logout operations.

Key components:
    - POST /auth/login: Authenticate and get access/refresh tokens
    - POST /auth/refresh: Exchange refresh token for new tokens
    - POST /auth/logout: Logout current user (logging only, JWT is stateless)

Dependencies:
    - app.services.auth_service: Authentication business logic
    - app.schemas.auth: Request/response schemas
    - app.api.deps: Dependency injection

Related files:
    - app/services/auth_service.py: Business logic
    - app/schemas/auth.py: LoginRequest, Token, RefreshTokenRequest
    - app/common/security.py: Token utilities

Common commands:
    - Test: uv run pytest tests/integration/test_auth.py -v
    - Try: http://localhost:8000/docs#/auth

Example:
    Login flow::

        # POST /api/v1/auth/login
        curl -X POST http://localhost:8000/api/v1/auth/login \\
            -H "Content-Type: application/json" \\
            -d '{"email": "user@example.com", "password": "password123"}'

        # Response
        {
            "access_token": "eyJ...",
            "refresh_token": "eyJ...",
            "token_type": "bearer"
        }

    Using tokens::

        # Include in Authorization header
        curl http://localhost:8000/api/v1/users/me \\
            -H "Authorization: Bearer eyJ..."

    Refresh flow::

        # POST /api/v1/auth/refresh
        curl -X POST http://localhost:8000/api/v1/auth/refresh \\
            -H "Content-Type: application/json" \\
            -d '{"refresh_token": "eyJ..."}'
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.auth import LoginRequest, Token, RefreshTokenRequest
from app.services.auth_service import AuthService
from app.api.deps import get_auth_service, CurrentUser
from app.common.logging import get_logger
from app.common.exceptions import AuthenticationError

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=Token,
    summary="Login",
    description="Login with email and password to get access and refresh tokens.",
)
async def login(
    credentials: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> Token:
    """Login with email/password."""
    try:
        return await auth_service.login(credentials)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
        )


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh token",
    description="Get a new access token using a refresh token.",
)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> Token:
    """Refresh access token using refresh token."""
    try:
        return await auth_service.refresh_access_token(request)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
        )


@router.post(
    "/logout",
    summary="Logout",
    description="Logout current user. Note: JWT is stateless, so this is mainly for logging purposes.",
)
async def logout(current_user: CurrentUser) -> dict[str, str]:
    """Logout current user."""
    logger.info("user_logout", user_id=str(current_user.id), email=current_user.email)
    return {"message": "Logged out successfully"}
