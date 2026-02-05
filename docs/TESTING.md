# Backend Testing Guide

Complete guide for testing FastAPI backend with pytest, including unit tests, integration tests, and best practices.

## Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Writing Unit Tests](#writing-unit-tests)
- [Writing Integration Tests](#writing-integration-tests)
- [Test Fixtures](#test-fixtures)
- [Mocking](#mocking)
- [Coverage](#coverage)
- [Best Practices](#best-practices)
- [Common Patterns](#common-patterns)
- [Troubleshooting](#troubleshooting)

---

## Overview

### Testing Stack

| Tool | Purpose |
|------|---------|
| **pytest** | Test framework |
| **pytest-asyncio** | Async test support |
| **pytest-cov** | Coverage reporting |
| **httpx** | HTTP client for API testing |
| **pytest-mock** | Mocking utilities |

### Test Types

1. **Unit Tests** - Test individual functions/methods in isolation
2. **Integration Tests** - Test complete request/response cycle through API
3. **Repository Tests** - Test database operations
4. **Service Tests** - Test business logic

---

## Test Structure

```
backend/
├── tests/
│ ├── conftest.py # Shared fixtures
│ ├── unit/ # Unit tests
│ │ ├── services/ # Service layer tests
│ │ │ ├── test_user_service.py
│ │ │ └── test_item_service.py
│ │ └── repositories/ # Repository tests
│ │ ├── test_user_repo.py
│ │ └── test_item_repo.py
│ └── integration/ # Integration tests
│ ├── api/ # API endpoint tests
│ │ ├── test_auth.py
│ │ ├── test_users.py
│ │ └── test_items.py
│ └── conftest.py # Integration-specific fixtures
```

---

## Running Tests

### Quick Commands

```bash
# Run all tests
cd backend
uv run pytest

# Run all tests with coverage
uv run test # Uses pyproject.toml script

# Run specific test file
uv run pytest tests/unit/services/test_user_service.py -v

# Run specific test function
uv run pytest tests/unit/services/test_user_service.py::test_create_user -v

# Run tests matching pattern
uv run pytest -k "user" -v

# Run only unit tests
uv run pytest tests/unit -v

# Run only integration tests
uv run pytest tests/integration -v

# Run with verbose output
uv run pytest -v

# Run with print statements visible
uv run pytest -s

# Stop on first failure
uv run pytest -x

# Run last failed tests only
uv run pytest --lf

# Show coverage in terminal
uv run pytest --cov=app --cov-report=term-missing
```

### Coverage Reports

```bash
# Generate HTML coverage report
uv run pytest --cov=app --cov-report=html
open htmlcov/index.html # View in browser

# Generate XML coverage (for CI)
uv run pytest --cov=app --cov-report=xml

# Coverage for specific module
uv run pytest --cov=app.services --cov-report=term-missing
```

---

## Writing Unit Tests

### Service Tests

Test business logic in isolation by mocking dependencies.

**Example**: `tests/unit/services/test_user_service.py`

```python
"""
Unit tests for UserService business logic.
"""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserUpdate
from app.models.user import User


@pytest.fixture
def mock_user_repo():
 """Mock UserRepository."""
 repo = AsyncMock()
 return repo


@pytest.fixture
def user_service(mock_user_repo):
 """UserService instance with mocked repository."""
 return UserService(mock_user_repo)


@pytest.fixture
def sample_user():
 """Sample user for tests."""
 return User(
 id=uuid4(),
 email="test@example.com",
 hashed_password="hashed",
 is_active=True,
 )


class TestCreateUser:
 """Tests for creating users."""

 @pytest.mark.asyncio
 async def test_create_user_success(self, user_service, mock_user_repo, sample_user):
 """Test successful user creation."""
 # Arrange
 user_data = UserCreate(email="test@example.com", password="password123")
 mock_user_repo.create.return_value = sample_user

 # Act
 result = await user_service.create_user(user_data)

 # Assert
 assert result.email == user_data.email
 mock_user_repo.create.assert_called_once()

 @pytest.mark.asyncio
 async def test_create_user_duplicate_email(self, user_service, mock_user_repo):
 """Test user creation with duplicate email."""
 # Arrange
 user_data = UserCreate(email="existing@example.com", password="password123")
 mock_user_repo.get_by_email.return_value = User(
 id=uuid4(), email=user_data.email, hashed_password="hashed"
 )

 # Act & Assert
 with pytest.raises(ValueError, match="Email already registered"):
 await user_service.create_user(user_data)


class TestUpdateUser:
 """Tests for updating users."""

 @pytest.mark.asyncio
 async def test_update_user_success(self, user_service, mock_user_repo, sample_user):
 """Test successful user update."""
 # Arrange
 user_id = sample_user.id
 update_data = UserUpdate(email="updated@example.com")
 mock_user_repo.get_by_id.return_value = sample_user
 mock_user_repo.update.return_value = sample_user

 # Act
 result = await user_service.update_user(user_id, update_data)

 # Assert
 assert result is not None
 mock_user_repo.update.assert_called_once()

 @pytest.mark.asyncio
 async def test_update_nonexistent_user(self, user_service, mock_user_repo):
 """Test updating user that doesn't exist."""
 # Arrange
 user_id = uuid4()
 update_data = UserUpdate(email="updated@example.com")
 mock_user_repo.get_by_id.return_value = None

 # Act & Assert
 with pytest.raises(ValueError, match="User not found"):
 await user_service.update_user(user_id, update_data)
```

### Repository Tests

Test database operations with real test database.

**Example**: `tests/unit/repositories/test_user_repo.py`

```python
"""
Unit tests for UserRepository database operations.
"""
import pytest
from uuid import uuid4

from app.repositories.user_repository import UserRepository
from app.models.user import User


@pytest.mark.asyncio
async def test_create_user(db_session):
 """Test creating a user in database."""
 # Arrange
 repo = UserRepository(db_session)
 user_data = {
 "email": "test@example.com",
 "hashed_password": "hashed_password",
 "is_active": True,
 }

 # Act
 user = await repo.create(User(**user_data))
 await db_session.commit()

 # Assert
 assert user.id is not None
 assert user.email == user_data["email"]
 assert user.is_active is True


@pytest.mark.asyncio
async def test_get_by_email(db_session):
 """Test retrieving user by email."""
 # Arrange
 repo = UserRepository(db_session)
 user = await repo.create(
 User(email="find@example.com", hashed_password="hashed", is_active=True)
 )
 await db_session.commit()

 # Act
 found_user = await repo.get_by_email("find@example.com")

 # Assert
 assert found_user is not None
 assert found_user.email == "find@example.com"
 assert found_user.id == user.id


@pytest.mark.asyncio
async def test_get_by_email_not_found(db_session):
 """Test retrieving non-existent user by email."""
 # Arrange
 repo = UserRepository(db_session)

 # Act
 found_user = await repo.get_by_email("nonexistent@example.com")

 # Assert
 assert found_user is None
```

---

## Writing Integration Tests

Test complete API request/response cycle.

**Example**: `tests/integration/api/test_users.py`

```python
"""
Integration tests for User API endpoints.
"""
import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_create_user_success(client: AsyncClient):
 """Test successful user creation via API."""
 # Arrange
 user_data = {
 "email": "newuser@example.com",
 "password": "password123",
 }

 # Act
 response = await client.post("/api/v1/users", json=user_data)

 # Assert
 assert response.status_code == 201
 data = response.json()
 assert data["email"] == user_data["email"]
 assert "id" in data
 assert "hashed_password" not in data # Password should not be returned


@pytest.mark.asyncio
async def test_create_user_duplicate_email(client: AsyncClient):
 """Test user creation with duplicate email."""
 # Arrange
 user_data = {
 "email": "duplicate@example.com",
 "password": "password123",
 }

 # Act
 response1 = await client.post("/api/v1/users", json=user_data)
 response2 = await client.post("/api/v1/users", json=user_data)

 # Assert
 assert response1.status_code == 201
 assert response2.status_code == 400
 assert "already registered" in response2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_user_requires_auth(client: AsyncClient):
 """Test getting user requires authentication."""
 # Act
 response = await client.get("/api/v1/users/me")

 # Assert
 assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, auth_headers):
 """Test getting current authenticated user."""
 # Act
 response = await client.get("/api/v1/users/me", headers=auth_headers)

 # Assert
 assert response.status_code == 200
 data = response.json()
 assert "email" in data
 assert "id" in data


@pytest.mark.asyncio
async def test_list_users_with_pagination(client: AsyncClient, auth_headers):
 """Test listing users with pagination."""
 # Act
 response = await client.get(
 "/api/v1/users?page=1&size=10",
 headers=auth_headers,
 )

 # Assert
 assert response.status_code == 200
 data = response.json()
 assert "items" in data
 assert "total" in data
 assert "page" in data
 assert "size" in data
 assert data["page"] == 1
 assert data["size"] == 10


@pytest.mark.asyncio
async def test_update_user_forbidden_for_other_user(
 client: AsyncClient, auth_headers, other_user
):
 """Test users cannot update other users."""
 # Arrange
 update_data = {"email": "hacker@example.com"}

 # Act
 response = await client.put(
 f"/api/v1/users/{other_user.id}",
 json=update_data,
 headers=auth_headers,
 )

 # Assert
 assert response.status_code == 403
```

---

## Test Fixtures

Common fixtures defined in `tests/conftest.py`:

```python
"""
Shared test fixtures for all tests.
"""
import asyncio
import pytest
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.db.postgres import Base, get_db
from app.models.user import User
from app.common.security import get_password_hash


# Database URL for tests (use separate test database)
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db"


@pytest.fixture(scope="session")
def event_loop():
 """Create event loop for async tests."""
 loop = asyncio.get_event_loop_policy().new_event_loop()
 yield loop
 loop.close()


@pytest.fixture(scope="session")
async def test_engine():
 """Create test database engine."""
 engine = create_async_engine(TEST_DATABASE_URL, echo=False)
 async with engine.begin() as conn:
 await conn.run_sync(Base.metadata.create_all)
 yield engine
 async with engine.begin() as conn:
 await conn.run_sync(Base.metadata.drop_all)
 await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
 """Create test database session."""
 async_session = async_sessionmaker(
 test_engine, class_=AsyncSession, expire_on_commit=False
 )
 async with async_session() as session:
 yield session
 await session.rollback()


@pytest.fixture
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
 """Create test HTTP client."""
 async def override_get_db():
 yield db_session

 app.dependency_overrides[get_db] = override_get_db

 async with AsyncClient(app=app, base_url="http://test") as ac:
 yield ac

 app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session) -> User:
 """Create test user."""
 user = User(
 email="test@example.com",
 hashed_password=get_password_hash("password123"),
 is_active=True,
 )
 db_session.add(user)
 await db_session.commit()
 await db_session.refresh(user)
 return user


@pytest.fixture
async def auth_headers(client: AsyncClient, test_user) -> dict:
 """Get authentication headers for test user."""
 response = await client.post(
 "/api/v1/auth/login",
 data={"username": test_user.email, "password": "password123"},
 )
 token = response.json()["access_token"]
 return {"Authorization": f"Bearer {token}"}
```

---

## Mocking

### Mocking External Services

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
@patch("app.services.email_service.send_email")
async def test_user_registration_sends_email(mock_send_email, user_service):
 """Test that user registration sends welcome email."""
 # Arrange
 mock_send_email.return_value = True
 user_data = UserCreate(email="new@example.com", password="password123")

 # Act
 await user_service.create_user(user_data)

 # Assert
 mock_send_email.assert_called_once()
 call_args = mock_send_email.call_args
 assert call_args[0][0] == "new@example.com"
 assert "Welcome" in call_args[0][1]
```

### Mocking Time

```python
from unittest.mock import patch
from datetime import datetime, UTC

@pytest.mark.asyncio
@patch("app.services.user_service.datetime")
async def test_user_created_at(mock_datetime, user_service):
 """Test user creation timestamp."""
 # Arrange
 fixed_time = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)
 mock_datetime.now.return_value = fixed_time

 # Act
 user = await user_service.create_user(UserCreate(email="test@example.com"))

 # Assert
 assert user.created_at == fixed_time
```

---

## Coverage

### Target Coverage

- **Overall**: 80%+ coverage
- **Critical Paths**: 100% (auth, permissions, payments)
- **Repositories**: 90%+
- **Services**: 85%+
- **API Endpoints**: 80%+

### Viewing Coverage

```bash
# Run tests with coverage
uv run pytest --cov=app --cov-report=html

# Open coverage report
open htmlcov/index.html
```

### Excluding from Coverage

Add to `pyproject.toml`:

```toml
[tool.coverage.run]
omit = [
 "app/main.py",
 "*/tests/*",
 "*/migrations/*",
]
```

---

## Best Practices

### DO

- [X] **Use descriptive test names**: `test_create_user_with_duplicate_email_raises_error`
- [X] **Follow AAA pattern**: Arrange → Act → Assert
- [X] **Test one thing per test**: Focused, single assertion when possible
- [X] **Use fixtures for common setup**: Reusable, consistent test data
- [X] **Test edge cases**: Empty inputs, invalid data, boundary conditions
- [X] **Test error paths**: Exceptions, validation failures
- [X] **Mock external dependencies**: Databases (in unit tests), APIs, file systems
- [X] **Use async fixtures for async code**: `@pytest.mark.asyncio`
- [X] **Clean up after tests**: Rollback database transactions

### DON'T

- [-] **Don't test framework code**: Trust FastAPI, SQLAlchemy work correctly
- [-] **Don't write brittle tests**: Avoid testing implementation details
- [-] **Don't share state between tests**: Each test should be independent
- [-] **Don't skip cleanup**: Always rollback or cleanup test data
- [-] **Don't test everything**: Focus on business logic, skip trivial code

---

## Common Patterns

### Testing Permissions

```python
@pytest.mark.asyncio
async def test_delete_user_requires_admin(client, user_auth_headers):
 """Test deleting user requires admin permission."""
 response = await client.delete(
 "/api/v1/users/some-id",
 headers=user_auth_headers, # Regular user, not admin
 )
 assert response.status_code == 403
 assert "permission" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_delete_user_as_admin(client, admin_auth_headers):
 """Test admin can delete users."""
 response = await client.delete(
 "/api/v1/users/some-id",
 headers=admin_auth_headers,
 )
 assert response.status_code == 204
```

### Testing Validation

```python
@pytest.mark.asyncio
async def test_create_user_invalid_email(client):
 """Test user creation with invalid email."""
 response = await client.post(
 "/api/v1/users",
 json={"email": "not-an-email", "password": "password123"},
 )
 assert response.status_code == 422
 errors = response.json()["detail"]
 assert any("email" in str(error).lower() for error in errors)
```

### Testing Pagination

```python
@pytest.mark.asyncio
async def test_list_items_pagination(client, auth_headers):
 """Test item list pagination."""
 # Create 25 items
 for i in range(25):
 await client.post(
 "/api/v1/items",
 json={"name": f"Item {i}"},
 headers=auth_headers,
 )

 # Get first page
 response = await client.get(
 "/api/v1/items?page=1&size=10",
 headers=auth_headers,
 )
 data = response.json()
 assert len(data["items"]) == 10
 assert data["total"] == 25
 assert data["pages"] == 3
```

---

## Troubleshooting

### Tests Hang

**Cause**: Async fixtures not properly cleaned up

**Solution**:
```python
@pytest.fixture
async def my_fixture():
 resource = await create_resource()
 yield resource
 await resource.cleanup() # Don't forget cleanup!
```

### Database Connection Errors

**Cause**: Test database not created or wrong URL

**Solution**:
```bash
# Create test database
createdb test_db

# Verify TEST_DATABASE_URL in conftest.py
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db"
```

### Tests Pass Individually But Fail Together

**Cause**: Tests sharing state or not cleaning up

**Solution**:
- Use database transactions that rollback
- Clear caches between tests
- Use fresh fixtures for each test

### Slow Tests

**Causes**:
- Too many database calls
- Not using fixtures efficiently
- Creating too much test data

**Solutions**:
```python
# Use session-scoped fixtures for expensive setup
@pytest.fixture(scope="session")
async def test_engine():
 ...

# Use class-level fixtures for grouped tests
@pytest.fixture(scope="class")
async def test_data():
 ...

# Mock slow external calls
@patch("app.services.slow_external_api")
async def test_feature(mock_api):
 ...
```

---

## Next Steps

- **E2E Testing**: See `docs/E2E_TESTING.md` for end-to-end tests
- **Frontend Testing**: See `frontend/docs/TESTING.md` for React tests
- **CI/CD**: See `docs/DEPLOYMENT.md` for running tests in CI

---

**Last Updated**: 2026-02-05
