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
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.schemas.auth import LoginRequest, Token, RefreshTokenRequest
from app.services.auth_service import AuthService
from app.api.deps import get_auth_service, CurrentUser
from app.common.logging import get_logger
from app.common.exceptions import AuthenticationError
from app.config import Settings, settings as global_settings

# Type alias for settings dependency
def get_settings() -> Settings:
    """Get settings instance."""
    return global_settings

logger = get_logger(__name__)

# Rate limiter instance
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=Token,
    summary="Login",
    description="Login with email and password. Returns tokens in JSON (for Swagger) and sets httpOnly cookies (for frontend). Rate limited to 5 requests/minute.",
)
@limiter.limit("5/minute")
async def login(
    request: Request,  # Required by slowapi for rate limiting
    response: Response,
    credentials: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
    settings: Annotated[Settings, Depends(get_settings)] = global_settings,
) -> Token:
    """
    Login with email/password (dual-mode auth).

    Returns:
    - JSON with access_token and refresh_token (for Swagger/API clients)
    - Sets httpOnly cookies with same tokens (for web frontend)

    Remember me: If true, refresh token expires in 30 days instead of 7.
    """
    try:
        tokens = await auth_service.login(credentials)

        # Determine refresh token max_age based on remember_me
        refresh_max_age = (
            settings.refresh_token_remember_me_expires_seconds
            if credentials.remember_me
            else settings.refresh_token_expires_seconds
        )

        # Set httpOnly cookies for frontend security
        response.set_cookie(
            key="access_token",
            value=tokens.access_token,
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite=settings.COOKIE_SAMESITE,
            max_age=settings.access_token_expires_seconds,
            path="/",
            domain=settings.COOKIE_DOMAIN,
        )

        response.set_cookie(
            key="refresh_token",
            value=tokens.refresh_token,
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite=settings.COOKIE_SAMESITE,
            max_age=refresh_max_age,
            path="/api/v1/auth/refresh",
            domain=settings.COOKIE_DOMAIN,
        )

        logger.info(
            "user_login_success",
            email=credentials.email,
            auth_mode="dual",
            remember_me=credentials.remember_me,
        )

        # Also return tokens in JSON for Swagger/API clients
        return tokens

    except AuthenticationError as e:
        logger.warning("login_failed", email=credentials.email, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
        )


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh token",
    description="Get new tokens. Accepts refresh_token from request body (API clients) or httpOnly cookie (frontend). Rate limited to 10 requests/minute.",
)
@limiter.limit("10/minute")
async def refresh_token(
    http_request: Request,  # Already present, used by slowapi too
    http_response: Response,
    request: RefreshTokenRequest | None = None,
    auth_service: AuthService = Depends(get_auth_service),
    settings: Annotated[Settings, Depends(get_settings)] = global_settings,
) -> Token:
    """
    Refresh tokens endpoint with dual-mode support.

    Accepts refresh_token from:
    1. Request body (for API clients) - optional
    2. HttpOnly cookie (for web frontend)

    Priority: Cookie > Request body
    """
    # Try cookie first (frontend)
    refresh_token_str = http_request.cookies.get("refresh_token")

    # Fallback to body (API clients)
    if not refresh_token_str and request:
        refresh_token_str = request.refresh_token

    if not refresh_token_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No refresh token provided",
        )

    try:
        # Create a RefreshTokenRequest object
        refresh_request = RefreshTokenRequest(refresh_token=refresh_token_str)
        new_tokens = await auth_service.refresh_access_token(refresh_request)

        # Set new cookies with config values
        http_response.set_cookie(
            key="access_token",
            value=new_tokens.access_token,
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite=settings.COOKIE_SAMESITE,
            max_age=settings.access_token_expires_seconds,
            path="/",
            domain=settings.COOKIE_DOMAIN,
        )

        http_response.set_cookie(
            key="refresh_token",
            value=new_tokens.refresh_token,
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite=settings.COOKIE_SAMESITE,
            max_age=settings.refresh_token_expires_seconds,
            path="/api/v1/auth/refresh",
            domain=settings.COOKIE_DOMAIN,
        )

        logger.info("token_refresh_success")
        return new_tokens

    except AuthenticationError as e:
        logger.warning("token_refresh_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
        )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout",
    description="Logout current user and clear httpOnly cookies.",
)
async def logout(
    response: Response,
    current_user: CurrentUser,
) -> None:
    """
    Logout endpoint - clears httpOnly cookies.

    Note: JWTs are stateless, so actual token invalidation happens
    via cookie deletion. For full security, implement token blacklist.
    """
    # Clear cookies by setting expired date
    response.set_cookie(
        key="access_token",
        value="",
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=0,  # Expire immediately
        path="/",
    )

    response.set_cookie(
        key="refresh_token",
        value="",
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=0,
        path="/api/v1/auth/refresh",
    )

    logger.info("user_logout", user_id=str(current_user.id), email=current_user.email)
    return None
