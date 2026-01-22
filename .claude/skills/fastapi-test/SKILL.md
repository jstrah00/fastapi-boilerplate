---
name: fastapi-test
description: Generate comprehensive unit and integration tests following project conventions
---

# FastAPI Test Generation

Create comprehensive tests following the project's testing patterns.

## Test Structure

```
tests/
├── conftest.py          # Shared fixtures
├── unit/                # Pure function tests (no DB)
│   └── test_security.py
└── integration/         # Full request/response tests
    └── test_auth.py
```

## Running Tests

```bash
# Run all tests with coverage
uv run test

# Run all tests (no coverage)
uv run pytest

# Run specific test file
uv run pytest tests/unit/test_security.py -v

# Run specific test class
uv run pytest tests/unit/test_security.py::TestPasswordHashing -v

# Run specific test
uv run pytest tests/unit/test_security.py::TestPasswordHashing::test_password_hash -v

# Run only unit tests
uv run pytest tests/unit -v

# Run only integration tests
uv run pytest tests/integration -v

# Run with extra verbosity
uv run pytest -vvs

# Run and stop on first failure
uv run pytest -x
```

## Available Fixtures (from conftest.py)

| Fixture | Description |
|---------|-------------|
| `db_session` | Fresh database session (tables created/dropped per test) |
| `client` | Async HTTP client for API requests |
| `test_user_data` | Dict with test user fields |
| `test_admin_data` | Dict with test admin fields |
| `test_user` | Created User model instance |
| `test_admin` | Created admin User model instance |
| `auth_headers` | `{"Authorization": "Bearer <token>"}` for test user |
| `admin_auth_headers` | `{"Authorization": "Bearer <token>"}` for admin |

## Unit Tests

Unit tests are for pure functions without database dependencies.

### Create `tests/unit/test_{resource}.py`

```python
"""
Unit tests for {resource} utilities.
"""
import pytest
from datetime import timedelta

# Import the functions you're testing
from app.common.security import get_password_hash, verify_password


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_password_hash_is_different_from_plain(self) -> None:
        """Hashed password should be different from plain text."""
        password = "mysecretpassword"
        hashed = get_password_hash(password)

        assert hashed != password

    def test_password_verification_success(self) -> None:
        """Correct password should verify successfully."""
        password = "mysecretpassword"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_password_verification_failure(self) -> None:
        """Wrong password should fail verification."""
        password = "mysecretpassword"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)

        assert verify_password(wrong_password, hashed) is False
```

### Unit Test Best Practices

1. **Test one thing per test** - clear, focused assertions
2. **Descriptive names** - `test_password_verification_success` not `test_password`
3. **Docstrings** - Explain what the test verifies
4. **No database** - Mock dependencies if needed
5. **Fast execution** - Unit tests should run in milliseconds

## Integration Tests

Integration tests verify the full request/response cycle.

### Create `tests/integration/test_{resources}.py`

```python
"""
Integration tests for {resource} API endpoints.
"""
import pytest
from httpx import AsyncClient
from uuid import UUID


pytestmark = pytest.mark.integration


class Test{Resource}Create:
    """Tests for creating {resources}."""

    async def test_create_{resource}_success(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Authenticated user should create {resource} successfully."""
        response = await client.post(
            "/api/v1/{resources}/",
            json={
                "title": "Test {Resource}",
                "description": "Test description",
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test {Resource}"
        assert data["description"] == "Test description"
        assert "id" in data
        assert data["status"] == "active"

    async def test_create_{resource}_unauthenticated(
        self,
        client: AsyncClient,
    ) -> None:
        """Unauthenticated request should fail."""
        response = await client.post(
            "/api/v1/{resources}/",
            json={"title": "Test", "description": "Test"},
        )

        assert response.status_code == 401

    async def test_create_{resource}_invalid_data(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Invalid data should return 422."""
        response = await client.post(
            "/api/v1/{resources}/",
            json={"title": ""},  # Empty title should fail validation
            headers=auth_headers,
        )

        assert response.status_code == 422


class Test{Resource}List:
    """Tests for listing {resources}."""

    async def test_list_{resources}_empty(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Empty list should return empty array."""
        response = await client.get(
            "/api/v1/{resources}/",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["{resources}"] == []
        assert data["total"] == 0

    async def test_list_{resources}_returns_owned(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """User should see their own {resources}."""
        # Create a {resource}
        create_response = await client.post(
            "/api/v1/{resources}/",
            json={"title": "My {Resource}"},
            headers=auth_headers,
        )
        assert create_response.status_code == 201

        # List {resources}
        response = await client.get(
            "/api/v1/{resources}/",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["{resources}"]) == 1
        assert data["{resources}"][0]["title"] == "My {Resource}"


class Test{Resource}Get:
    """Tests for getting a single {resource}."""

    async def test_get_{resource}_success(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Owner should get their {resource}."""
        # Create {resource}
        create_response = await client.post(
            "/api/v1/{resources}/",
            json={"title": "Test {Resource}"},
            headers=auth_headers,
        )
        {resource}_id = create_response.json()["id"]

        # Get {resource}
        response = await client.get(
            f"/api/v1/{resources}/{{{resource}_id}}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["id"] == {resource}_id

    async def test_get_{resource}_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Non-existent {resource} should return 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(
            f"/api/v1/{resources}/{fake_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_get_{resource}_not_owner(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        admin_auth_headers: dict[str, str],
    ) -> None:
        """Non-owner (non-admin) should get 403."""
        # Create {resource} as user
        create_response = await client.post(
            "/api/v1/{resources}/",
            json={"title": "User's {Resource}"},
            headers=auth_headers,
        )
        {resource}_id = create_response.json()["id"]

        # Try to get as different user (need another user fixture)
        # For now, verify admin CAN access
        response = await client.get(
            f"/api/v1/{resources}/{{{resource}_id}}",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200  # Admin can access


class Test{Resource}Update:
    """Tests for updating {resources}."""

    async def test_update_{resource}_success(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Owner should update their {resource}."""
        # Create
        create_response = await client.post(
            "/api/v1/{resources}/",
            json={"title": "Original"},
            headers=auth_headers,
        )
        {resource}_id = create_response.json()["id"]

        # Update
        response = await client.patch(
            f"/api/v1/{resources}/{{{resource}_id}}",
            json={"title": "Updated"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["title"] == "Updated"

    async def test_update_{resource}_partial(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Partial update should only change provided fields."""
        # Create with description
        create_response = await client.post(
            "/api/v1/{resources}/",
            json={"title": "Original", "description": "Keep this"},
            headers=auth_headers,
        )
        {resource}_id = create_response.json()["id"]

        # Update only title
        response = await client.patch(
            f"/api/v1/{resources}/{{{resource}_id}}",
            json={"title": "New Title"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title"
        assert data["description"] == "Keep this"  # Unchanged


class Test{Resource}Delete:
    """Tests for deleting {resources}."""

    async def test_delete_{resource}_success(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Owner should delete their {resource}."""
        # Create
        create_response = await client.post(
            "/api/v1/{resources}/",
            json={"title": "To Delete"},
            headers=auth_headers,
        )
        {resource}_id = create_response.json()["id"]

        # Delete
        response = await client.delete(
            f"/api/v1/{resources}/{{{resource}_id}}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        # Verify deleted (soft delete - should return 404)
        get_response = await client.get(
            f"/api/v1/{resources}/{{{resource}_id}}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404

    async def test_delete_{resource}_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Deleting non-existent {resource} should return 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.delete(
            f"/api/v1/{resources}/{fake_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404
```

## Adding Custom Fixtures

Add to `tests/conftest.py`:

```python
@pytest.fixture
async def test_{resource}(
    db_session: AsyncSession,
    test_user: Any,
) -> Any:
    """Create a test {resource} in the database."""
    from app.models.postgres.{resource} import {Resource}

    {resource} = {Resource}(
        title="Test {Resource}",
        description="Test description",
        owner_id=test_user.id,
        status="active",
    )
    db_session.add({resource})
    await db_session.commit()
    await db_session.refresh({resource})
    return {resource}


@pytest.fixture
def {resource}_data() -> dict[str, Any]:
    """Test {resource} data for creating test {resources}."""
    return {
        "title": "Test {Resource}",
        "description": "Test description",
    }
```

## Testing Service Layer

```python
"""
Unit tests for {resource} service.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.services.{resource}_service import {Resource}Service
from app.common.exceptions import NotFoundError, ValidationError


class Test{Resource}Service:
    """Tests for {Resource}Service."""

    @pytest.fixture
    def mock_repo(self) -> AsyncMock:
        """Create mock repository."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_repo: AsyncMock) -> {Resource}Service:
        """Create service with mock repo."""
        return {Resource}Service(mock_repo)

    @pytest.fixture
    def mock_user(self) -> MagicMock:
        """Create mock user."""
        user = MagicMock()
        user.id = uuid4()
        user.is_admin = False
        return user

    async def test_get_{resource}_not_found(
        self,
        service: {Resource}Service,
        mock_repo: AsyncMock,
        mock_user: MagicMock,
    ) -> None:
        """Should raise NotFoundError for missing {resource}."""
        mock_repo.get.return_value = None

        with pytest.raises(NotFoundError):
            await service.get_{resource}(uuid4(), mock_user)

    async def test_get_{resource}_not_owner(
        self,
        service: {Resource}Service,
        mock_repo: AsyncMock,
        mock_user: MagicMock,
    ) -> None:
        """Should raise ValidationError for non-owner."""
        mock_{resource} = MagicMock()
        mock_{resource}.owner_id = uuid4()  # Different owner
        mock_{resource}.status = "active"
        mock_repo.get.return_value = mock_{resource}

        with pytest.raises(ValidationError):
            await service.get_{resource}(uuid4(), mock_user)
```

## Test Patterns

### Testing Validation Errors

```python
async def test_create_with_invalid_email(
    self,
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Invalid email should return 422."""
    response = await client.post(
        "/api/v1/users/",
        json={
            "email": "not-an-email",
            "password": "password123",
            "first_name": "Test",
            "last_name": "User",
        },
        headers=auth_headers,
    )

    assert response.status_code == 422
    errors = response.json()["details"]
    assert any("email" in str(e).lower() for e in errors)
```

### Testing Permission Errors

```python
async def test_admin_only_endpoint(
    self,
    client: AsyncClient,
    auth_headers: dict[str, str],  # Regular user
) -> None:
    """Non-admin should get 403."""
    response = await client.get(
        "/api/v1/users/",  # Admin-only endpoint
        headers=auth_headers,
    )

    assert response.status_code == 403
```

### Testing Pagination

```python
async def test_pagination(
    self,
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Pagination should work correctly."""
    # Create multiple items
    for i in range(5):
        await client.post(
            "/api/v1/{resources}/",
            json={"title": f"{Resource} {i}"},
            headers=auth_headers,
        )

    # Get first page
    response = await client.get(
        "/api/v1/{resources}/?skip=0&limit=2",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["{resources}"]) == 2
    assert data["total"] == 5
    assert data["skip"] == 0
    assert data["limit"] == 2
```

## Checklist for Tests

- [ ] Unit tests for pure functions (no DB)
- [ ] Integration tests for all CRUD endpoints
- [ ] Test authentication required
- [ ] Test authorization (owner, admin)
- [ ] Test validation errors (422)
- [ ] Test not found (404)
- [ ] Test forbidden (403)
- [ ] Test partial updates
- [ ] Test pagination
- [ ] Custom fixtures added to conftest.py
- [ ] All tests passing: `uv run test`
