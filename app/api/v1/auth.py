"""
Authentication API endpoints.

# =============================================================================
# AUTH API: Login, token refresh, and logout.
# =============================================================================
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
