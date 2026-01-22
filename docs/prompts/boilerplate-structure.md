# FastAPI Boilerplate Structure

Complete architecture and patterns documentation for the Feature Planner Project.

Upload this file to your Claude.ai Project as project knowledge.

---

## Directory Structure
```
app/
├── api/
│   ├── v1/
│   │   ├── auth.py          # JWT authentication endpoints
│   │   ├── users.py         # User CRUD
│   │   └── items.py         # Example resource
│   ├── deps.py              # Dependency injection functions
│   └── handlers.py          # Global exception handlers
│
├── common/
│   ├── exceptions.py        # Custom exception classes
│   ├── logging.py           # Structured logging (structlog)
│   ├── permissions.py       # RBAC: Permission enum, Role enum, ROLE_PERMISSIONS
│   ├── security.py          # JWT creation, password hashing
│   └── alerts.py            # Telegram alerts (optional)
│
├── db/
│   ├── postgres.py          # PostgreSQL AsyncEngine, async_session_maker
│   ├── mongodb.py           # MongoDB client, Beanie initialization
│   └── unit_of_work.py      # Cross-database transaction management
│
├── models/
│   ├── postgres/
│   │   ├── user.py          # User model (SQLAlchemy)
│   │   └── item.py          # Item model (example)
│   └── mongodb/
│       └── document.py      # Example Beanie document
│
├── repositories/
│   ├── base.py              # BaseRepository with generic CRUD
│   ├── user_repo.py         # UserRepository
│   └── item_repo.py         # ItemRepository
│
├── schemas/
│   ├── auth.py              # Login, Token, TokenRefresh DTOs
│   ├── user.py              # UserCreate, UserUpdate, UserResponse
│   └── item.py              # Item DTOs
│
├── services/
│   ├── auth_service.py      # Authentication logic
│   ├── user_service.py      # User business logic
│   └── item_service.py      # Item business logic
│
├── config.py                # Pydantic Settings (env vars)
└── main.py                  # FastAPI app, CORS, middleware, routers

tests/
├── conftest.py              # Pytest fixtures (client, db, auth)
├── unit/                    # Unit tests (isolated)
└── integration/             # Integration tests (full stack)

alembic/
├── env.py                   # Alembic config (imports all models)
└── versions/                # Migration files

scripts/
└── init_db.py               # Initialize DB with admin user
```

## Key Patterns

### 1. PostgreSQL Models (app/models/postgres/)
```python
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.db.postgres import Base

class Example(Base):
    __tablename__ = "examples"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships (always bidirectional)
    user = relationship("User", back_populates="examples")
```

Key conventions:
- Extends `Base` from app.db.postgres
- Use `__tablename__` explicitly
- Index frequently queried columns
- Always use type hints in relationships
- Bidirectional relationships with back_populates

### 2. MongoDB Documents (app/models/mongodb/)
```python
from beanie import Document
from pydantic import Field
from datetime import datetime, timezone

class ExampleDocument(Document):
    name: str
    user_id: str  # Reference to PostgreSQL user (no FK)
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Settings:
        name = "examples"  # Collection name
        indexes = ["user_id", "created_at"]
```

Key conventions:
- Extends `Document` from Beanie
- Use Pydantic Field for defaults
- No foreign keys (cross-database references use IDs as strings)
- Specify indexes in Settings
- Register in app/db/mongodb.py init_mongodb()

### 3. Schemas (app/schemas/)
```python
from pydantic import BaseModel, Field, validator

class ExampleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None

class ExampleCreate(ExampleBase):
    user_id: int

class ExampleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None

class ExampleResponse(ExampleBase):
    id: int
    user_id: int
    is_active: bool
    
    class Config:
        from_attributes = True  # For SQLAlchemy models
```

Key conventions:
- Use Field for validation
- Separate Create/Update/Response schemas
- Config.from_attributes for ORM models
- Use | None for optional fields (Python 3.10+)
- Custom validators when needed

### 4. Repositories (app/repositories/)

PostgreSQL Repository:
```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.postgres.example import Example

class ExampleRepository(BaseRepository[Example]):
    def __init__(self, session: AsyncSession):
        super().__init__(Example, session)
    
    async def get_by_user(self, user_id: int) -> list[Example]:
        result = await self.session.execute(
            select(Example).where(Example.user_id == user_id)
        )
        return result.scalars().all()
```

MongoDB Repository:
```python
from app.models.mongodb.example import ExampleDocument

class ExampleMongoRepository:
    async def get_by_user(self, user_id: str) -> list[ExampleDocument]:
        return await ExampleDocument.find(
            ExampleDocument.user_id == user_id
        ).to_list()
    
    async def create(self, data: dict) -> ExampleDocument:
        doc = ExampleDocument(**data)
        await doc.insert()
        return doc
```

Key conventions:
- PostgreSQL: Extend BaseRepository
- MongoDB: Direct Beanie queries
- Type hints on all methods
- Async everywhere

### 5. Services (app/services/)
```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.example_repo import ExampleRepository
from app.schemas.example import ExampleCreate, ExampleUpdate
from app.common.exceptions import NotFoundError

class ExampleService:
    def __init__(self, session: AsyncSession):
        self.repo = ExampleRepository(session)
    
    async def create_example(self, data: ExampleCreate) -> Example:
        # Business logic here
        # Validation
        # Error handling
        return await self.repo.create(data.model_dump())
    
    async def get_example(self, example_id: int) -> Example:
        example = await self.repo.get(example_id)
        if not example:
            raise NotFoundError(f"Example {example_id} not found")
        return example
```

Key conventions:
- Accept session in __init__
- Instantiate repositories
- Business logic and validation here
- Raise custom exceptions from app.common.exceptions
- Return models, not schemas

### 6. API Routers (app/api/v1/)
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user, require_permissions
from app.services.example_service import ExampleService
from app.schemas.example import ExampleCreate, ExampleResponse
from app.common.permissions import Permission
from app.models.postgres.user import User

router = APIRouter(prefix="/examples", tags=["examples"])

@router.post("/", response_model=ExampleResponse)
async def create_example(
    data: ExampleCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions(Permission.EXAMPLES_CREATE))
):
    service = ExampleService(session)
    example = await service.create_example(data)
    return example

@router.get("/{example_id}", response_model=ExampleResponse)
async def get_example(
    example_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ExampleService(session)
    return await service.get_example(example_id)
```

Key conventions:
- Use APIRouter with prefix and tags
- Dependencies: get_db for session, get_current_user or require_permissions
- Instantiate service in endpoint
- Return models directly (FastAPI converts via response_model)
- Async def everywhere

### 7. Permissions (app/common/permissions.py)
```python
from enum import Enum

class Permission(str, Enum):
    # User permissions
    USERS_READ = "users:read"
    USERS_CREATE = "users:create"
    USERS_UPDATE = "users:update"
    USERS_DELETE = "users:delete"
    
    # Example permissions
    EXAMPLES_READ = "examples:read"
    EXAMPLES_CREATE = "examples:create"

class Role(str, Enum):
    ADMIN = "admin"
    USER = "user"

ROLE_PERMISSIONS = {
    Role.ADMIN: {
        Permission.USERS_READ,
        Permission.USERS_CREATE,
        Permission.USERS_UPDATE,
        Permission.USERS_DELETE,
        Permission.EXAMPLES_READ,
        Permission.EXAMPLES_CREATE,
    },
    Role.USER: {
        Permission.EXAMPLES_READ,
    },
}
```

Usage in endpoints:
```python
@router.get("/admin/users")
async def admin_list_users(
    current_user: User = Depends(require_permissions(Permission.USERS_READ))
):
    ...
```

### 8. Unit of Work (Cross-Database Transactions)
```python
from app.db.unit_of_work import UnitOfWork

async def create_user_with_profile(user_data: dict, profile_data: dict):
    async with UnitOfWork() as uow:
        # PostgreSQL operation
        user = await uow.user_repo.create(user_data)
        
        # MongoDB operation
        profile_data["user_id"] = str(user.id)
        await uow.profile_repo.create(profile_data)
        
        # Commit both
        await uow.commit()
    return user
```

When to use:
- Feature updates both PostgreSQL AND MongoDB
- Need transactional consistency across databases
- Rollback needed if either operation fails

### 9. Testing (tests/)
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_example(
    client: AsyncClient,
    test_user,
    auth_headers
):
    response = await client.post(
        "/api/v1/examples/",
        json={"name": "Test", "user_id": test_user.id},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Test"

@pytest.mark.asyncio
async def test_create_example_permission_denied(
    client: AsyncClient,
    test_user_no_perms,
    auth_headers_no_perms
):
    response = await client.post(
        "/api/v1/examples/",
        json={"name": "Test", "user_id": test_user_no_perms.id},
        headers=auth_headers_no_perms
    )
    assert response.status_code == 403
```

Fixtures available (conftest.py):
- `client`: AsyncClient for API testing
- `test_user`: User with standard permissions
- `test_admin`: User with admin role
- `auth_headers`: Headers with valid JWT
- `db_session`: PostgreSQL session
- `mongodb_client`: MongoDB client

## Common Commands
```bash
# Development
uv run dev                    # Start dev server
uv run ipython               # Python shell

# Database
uv run alembic upgrade head                           # Apply migrations
uv run alembic revision --autogenerate -m "message"  # Create migration
uv run alembic downgrade -1                          # Revert migration
uv run python scripts/init_db.py                     # Seed admin user

# Testing
uv run test                  # Run all tests with coverage
uv run pytest tests/unit -v # Unit tests only
uv run pytest -k test_name  # Specific test

# Code quality
uv run ruff format app tests # Format code
uv run ruff check app tests  # Lint
uv run mypy app              # Type check
```

## Examples to Reference

PostgreSQL CRUD:
- Model: app/models/postgres/user.py
- Schema: app/schemas/user.py
- Repository: app/repositories/user_repo.py
- Service: app/services/user_service.py
- Router: app/api/v1/users.py
- Tests: tests/integration/test_users.py

MongoDB Document:
- Document: app/models/mongodb/document.py
- Use Beanie queries directly

Authentication:
- app/api/v1/auth.py (login, refresh, register)
- app/common/security.py (JWT creation, password hashing)
- app/services/auth_service.py (auth business logic)

RBAC:
- app/common/permissions.py (Permission, Role, ROLE_PERMISSIONS)
- app/api/deps.py (require_permissions dependency)

Always follow these patterns when implementing new features.
