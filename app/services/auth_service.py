"""
Authentication service with business logic.

# =============================================================================
# SERVICE LAYER: Handles authentication operations.
# =============================================================================
"""
from uuid import UUID

from app.repositories.user_repo import UserRepository
from app.models.postgres.user import User
from app.schemas.auth import LoginRequest, Token, RefreshTokenRequest
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.logging import get_logger
from app.core.exceptions import AuthenticationError, NotFoundError

logger = get_logger(__name__)


class AuthService:
    """
    Service for authentication business logic.

    Handles:
    - Login (email/password)
    - Token refresh
    - Token validation
    """

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def login(self, credentials: LoginRequest) -> Token:
        """
        Login with email and password.

        Args:
            credentials: Login credentials (email + password)

        Returns:
            Access and refresh tokens

        Raises:
            AuthenticationError: If credentials are invalid
        """
        # Get user by email
        user = await self.user_repo.get_by_email(credentials.email)

        if not user:
            logger.warning("login_failed", email=credentials.email, reason="user_not_found")
            raise AuthenticationError(
                message="Invalid email or password",
                details={"email": credentials.email},
            )

        # Verify password
        if not verify_password(credentials.password, user.password_hash):
            logger.warning("login_failed", email=credentials.email, reason="invalid_password")
            raise AuthenticationError(
                message="Invalid email or password",
                details={"email": credentials.email},
            )

        # Check if user is active
        if user.status != "active":
            logger.warning("login_failed", email=credentials.email, reason="user_not_active")
            raise AuthenticationError(
                message="User account is not active",
                details={"email": credentials.email, "status": user.status},
            )

        # Create tokens
        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))

        logger.info(
            "login_success",
            user_id=str(user.id),
            email=user.email,
        )

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    async def refresh_access_token(self, request: RefreshTokenRequest) -> Token:
        """
        Refresh access token using refresh token.

        Args:
            request: Refresh token request

        Returns:
            New access and refresh tokens

        Raises:
            AuthenticationError: If refresh token is invalid
        """
        # Decode refresh token
        payload = decode_token(request.refresh_token)

        if payload is None:
            logger.warning("refresh_failed", reason="invalid_token")
            raise AuthenticationError(
                message="Invalid refresh token",
                details={},
            )

        # Check token type
        if payload.get("type") != "refresh":
            logger.warning("refresh_failed", reason="wrong_token_type")
            raise AuthenticationError(
                message="Invalid token type",
                details={},
            )

        # Get user ID
        user_id_str = payload.get("sub")
        if not user_id_str:
            logger.warning("refresh_failed", reason="missing_user_id")
            raise AuthenticationError(
                message="Invalid token payload",
                details={},
            )

        try:
            user_id = UUID(user_id_str)
        except ValueError:
            logger.warning("refresh_failed", reason="invalid_user_id", user_id=user_id_str)
            raise AuthenticationError(
                message="Invalid user ID in token",
                details={},
            )

        # Get user
        user = await self.user_repo.get(user_id)
        if not user:
            logger.warning("refresh_failed", reason="user_not_found", user_id=user_id_str)
            raise NotFoundError(
                message="User not found",
                details={"user_id": user_id_str},
            )

        # Check if user is active
        if user.status != "active":
            logger.warning("refresh_failed", reason="user_not_active", user_id=user_id_str)
            raise AuthenticationError(
                message="User account is not active",
                details={"user_id": user_id_str},
            )

        # Create new tokens
        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))

        logger.info("token_refreshed", user_id=str(user.id))

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    async def validate_token(self, token: str) -> User:
        """
        Validate access token and return user.

        Args:
            token: JWT access token

        Returns:
            User associated with the token

        Raises:
            AuthenticationError: If token is invalid
        """
        payload = decode_token(token)

        if payload is None or payload.get("type") != "access":
            raise AuthenticationError(
                message="Invalid access token",
                details={},
            )

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise AuthenticationError(
                message="Invalid token payload",
                details={},
            )

        try:
            user_id = UUID(user_id_str)
        except ValueError:
            raise AuthenticationError(
                message="Invalid user ID in token",
                details={},
            )

        user = await self.user_repo.get(user_id)
        if not user:
            raise NotFoundError(
                message="User not found",
                details={"user_id": user_id_str},
            )

        return user
