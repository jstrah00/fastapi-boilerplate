"""
Integration tests for authentication endpoints.

# =============================================================================
# EXAMPLE: Integration tests for the auth API.
#
# These tests require a database connection and test the full request/response
# cycle through the API.
# =============================================================================
"""
import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.integration


class TestAuthLogin:
    """Tests for the login endpoint."""

    async def test_login_success(
        self,
        client: AsyncClient,
        test_user: any,
        test_user_data: dict,
    ) -> None:
        """Successful login should return access and refresh tokens."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(
        self,
        client: AsyncClient,
        test_user: any,
        test_user_data: dict,
    ) -> None:
        """Login with wrong password should fail."""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401

    async def test_login_nonexistent_user(
        self,
        client: AsyncClient,
    ) -> None:
        """Login with nonexistent user should fail."""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "somepassword",
            },
        )

        assert response.status_code == 401


class TestAuthRefresh:
    """Tests for the token refresh endpoint."""

    async def test_refresh_token_success(
        self,
        client: AsyncClient,
        test_user: any,
        test_user_data: dict,
    ) -> None:
        """Valid refresh token should return new access token."""
        # First, login to get tokens
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"],
            },
        )
        refresh_token = login_response.json()["refresh_token"]

        # Then, refresh
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    async def test_refresh_invalid_token(
        self,
        client: AsyncClient,
    ) -> None:
        """Invalid refresh token should fail."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )

        assert response.status_code == 401


class TestAuthMe:
    """Tests for the current user endpoint."""

    async def test_get_current_user(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_user_data: dict,
    ) -> None:
        """Authenticated user should get their info."""
        response = await client.get(
            "/api/v1/users/me",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["first_name"] == test_user_data["first_name"]

    async def test_get_current_user_no_auth(
        self,
        client: AsyncClient,
    ) -> None:
        """Unauthenticated request should fail."""
        response = await client.get("/api/v1/users/me")

        assert response.status_code == 401
