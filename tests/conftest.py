"""
Pytest configuration and fixtures.

# =============================================================================
# TEST CONFIGURATION: Shared fixtures for all tests.
#
# CUSTOMIZATION:
# - Add database fixtures for integration tests
# - Add authentication fixtures
# - Add factory fixtures using factory_boy
# =============================================================================
"""
import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.db.postgres import Base, get_db
from app.config import settings
from app.core.security import get_password_hash


# =============================================================================
# Event Loop Configuration
# =============================================================================

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Database Fixtures
# =============================================================================

# Test database URL - uses the same DB with a test prefix
# In production, you might want a separate test database
TEST_DATABASE_URL = settings.postgres_url.replace(
    settings.POSTGRES_DB,
    f"test_{settings.POSTGRES_DB}"
)

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
    echo=False,
)

# Create test session factory
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database session for each test.

    This fixture:
    1. Creates all tables before each test
    2. Yields a session for the test to use
    3. Rolls back and drops tables after the test
    """
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()

    # Drop tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def override_get_db(db_session: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    """Override the get_db dependency with test session."""
    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    yield db_session
    app.dependency_overrides.clear()


# =============================================================================
# HTTP Client Fixtures
# =============================================================================

@pytest.fixture(scope="function")
async def client(override_get_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async HTTP client for testing API endpoints.

    Example:
        async def test_health(client: AsyncClient):
            response = await client.get("/health")
            assert response.status_code == 200
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# =============================================================================
# Authentication Fixtures
# =============================================================================

@pytest.fixture
def test_user_data() -> dict[str, Any]:
    """Test user data for creating test users."""
    return {
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "testpassword123",
        "role": "user",
    }


@pytest.fixture
def test_admin_data() -> dict[str, Any]:
    """Test admin data for creating test admins."""
    return {
        "email": "admin@example.com",
        "first_name": "Admin",
        "last_name": "User",
        "password": "adminpassword123",
        "role": "admin",
    }


@pytest.fixture
async def test_user(
    db_session: AsyncSession,
    test_user_data: dict[str, Any],
) -> Any:
    """
    Create a test user in the database.

    Returns the User model instance.
    """
    from app.models.postgres.user import User

    user = User(
        email=test_user_data["email"],
        first_name=test_user_data["first_name"],
        last_name=test_user_data["last_name"],
        password_hash=get_password_hash(test_user_data["password"]),
        role=test_user_data["role"],
        status="active",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_admin(
    db_session: AsyncSession,
    test_admin_data: dict[str, Any],
) -> Any:
    """
    Create a test admin in the database.

    Returns the User model instance.
    """
    from app.models.postgres.user import User

    admin = User(
        email=test_admin_data["email"],
        first_name=test_admin_data["first_name"],
        last_name=test_admin_data["last_name"],
        password_hash=get_password_hash(test_admin_data["password"]),
        role=test_admin_data["role"],
        status="active",
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest.fixture
async def auth_headers(
    client: AsyncClient,
    test_user: Any,
    test_user_data: dict[str, Any],
) -> dict[str, str]:
    """
    Get authentication headers for a test user.

    Returns headers dict with Authorization: Bearer <token>
    """
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user_data["email"],
            "password": test_user_data["password"],
        },
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def admin_auth_headers(
    client: AsyncClient,
    test_admin: Any,
    test_admin_data: dict[str, Any],
) -> dict[str, str]:
    """
    Get authentication headers for a test admin.

    Returns headers dict with Authorization: Bearer <token>
    """
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": test_admin_data["email"],
            "password": test_admin_data["password"],
        },
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# Factory Fixtures (using factory_boy)
# =============================================================================

# CUSTOMIZATION: Add factory_boy factories here for generating test data
# Example:
#
# from factory import Factory, Faker, LazyAttribute
#
# class UserFactory(Factory):
#     class Meta:
#         model = User
#
#     email = Faker("email")
#     first_name = Faker("first_name")
#     last_name = Faker("last_name")
#     password_hash = LazyAttribute(lambda _: get_password_hash("password"))
#     role = "user"
#     status = "active"
