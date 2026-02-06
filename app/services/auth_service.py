"""
Authentication service with business logic.

Handles user authentication including login, token refresh, and token validation.
Enforces authentication rules and coordinates between security utilities and user data.

Key components:
    - AuthService: Service class for authentication operations
    - login: Authenticate with email/password, return tokens
    - refresh_access_token: Exchange refresh token for new tokens (with rotation)
    - validate_token: Decode token and return associated user

Security features:
    - Single-use refresh tokens (token rotation)
    - Blacklist for used/revoked tokens
    - Prevents token reuse attacks

Dependencies:
    - app.repositories.user_repo: User data access
    - app.repositories.refresh_token_blacklist_repository: Blacklist operations
    - app.common.security: Token creation and password verification
    - app.common.exceptions: Authentication errors

Related files:
    - app/api/v1/auth.py: Authentication endpoints
    - app/api/deps.py: get_current_user dependency
    - app/common/security.py: Token utilities
    - app/schemas/auth.py: Request/response schemas
    - app/models/postgres/refresh_token_blacklist.py: Blacklist model

Common commands:
    - Test: uv run pytest tests/integration/test_auth.py -v
    - Cleanup blacklist: uv run cleanup-blacklist

Example:
    Login flow::

        auth_service = AuthService(user_repo, blacklist_repo)

        # Login with credentials
        tokens = await auth_service.login(LoginRequest(
            email="user@example.com",
            password="password123"
        ))
        # Returns Token(access_token="...", refresh_token="...", token_type="bearer")

    Refresh flow with rotation::

        # First use - works, old token blacklisted
        new_tokens = await auth_service.refresh_access_token(RefreshTokenRequest(
            refresh_token="eyJ..."
        ))

        # Second use - fails (token already blacklisted)
        await auth_service.refresh_access_token(RefreshTokenRequest(
            refresh_token="eyJ..."  # Same token
        ))
        # Raises AuthenticationError("Token has already been used")

    Token validation (used by get_current_user)::

        user = await auth_service.validate_token(access_token)
        # Returns User model if valid, raises AuthenticationError if invalid
"""
from datetime import datetime
from uuid import UUID

from app.repositories.user_repo import UserRepository
from app.repositories.refresh_token_blacklist_repository import (
    RefreshTokenBlacklistRepository,
)
from app.models.postgres.user import User
from app.schemas.auth import LoginRequest, Token, RefreshTokenRequest
from app.common.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.common.logging import get_logger
from app.common.exceptions import AuthenticationError, NotFoundError

logger = get_logger(__name__)


class AuthService:
    """
    Service for authentication business logic.

    Handles:
    - Login (email/password)
    - Token refresh with rotation (single-use tokens)
    - Token validation
    - Blacklist management
    """

    def __init__(
        self,
        user_repo: UserRepository,
        blacklist_repo: RefreshTokenBlacklistRepository,
    ):
        """
        Initialize AuthService with dependencies.

        Args:
            user_repo: Repository for user data access
            blacklist_repo: Repository for token blacklist operations
        """
        self.user_repo = user_repo
        self.blacklist_repo = blacklist_repo

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
        Refresh access token with single-use refresh tokens (token rotation).

        Security improvements:
        1. Check if token is blacklisted (prevents reuse)
        2. Add old token to blacklist
        3. Generate new access + refresh tokens

        Args:
            request: Refresh token request

        Returns:
            New access and refresh tokens

        Raises:
            AuthenticationError: If refresh token is invalid or already used

        Example:
            >>> # First use - works
            >>> tokens = await service.refresh_access_token(request)

            >>> # Second use - fails
            >>> await service.refresh_access_token(request)
            AuthenticationError: Token has already been used
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
            logger.warning("refresh_failed", reason="wrong_token_type", type=payload.get("type"))
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

        # =====================================================================
        # CHECK BLACKLIST - Prevent token reuse
        # =====================================================================
        is_blacklisted = await self.blacklist_repo.is_blacklisted(request.refresh_token)
        if is_blacklisted:
            logger.warning(
                "blacklisted_token_reuse_attempt",
                user_id=user_id_str,
                message="Refresh token has already been used",
            )
            raise AuthenticationError(
                message="Token has already been used",
                details={"reason": "token_reused"},
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

        # =====================================================================
        # ADD TO BLACKLIST - Mark old token as used
        # =====================================================================
        expires_at = datetime.fromtimestamp(payload.get("exp", 0))
        await self.blacklist_repo.add_to_blacklist(
            token=request.refresh_token,
            user_id=user_id,
            expires_at=expires_at,
            reason="used",
        )

        # =====================================================================
        # Generate NEW tokens (both access and refresh)
        # =====================================================================
        new_access_token = create_access_token(subject=str(user.id))
        new_refresh_token = create_refresh_token(subject=str(user.id))

        logger.info(
            "token_refresh_success",
            user_id=user_id_str,
            old_token_blacklisted=True,
            email=user.email,
        )

        return Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
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
