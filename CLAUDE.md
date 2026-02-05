# CLAUDE.md - FastAPI Boilerplate with PostgreSQL + MongoDB

## Quick Start
```bash
uv sync && cp .env.example .env
docker compose up -d postgres mongodb
uv run alembic upgrade head
uv run python scripts/init_db.py # Creates admin@example.com / admin123
uv run dev # http://localhost:8000
```

## Environment Configuration

**Required variables** (edit `.env` after copying from `.env.example`):
```bash
# Security (MUST change in production)
SECRET_KEY=your-secret-key-here # Generate with: openssl rand -hex 32

# Database URLs
DATABASE_URL=postgresql://user:pass@localhost:5432/db_name
MONGODB_URL=mongodb://localhost:27017/db_name

# CORS (frontend URLs)
BACKEND_CORS_ORIGINS=["http://localhost:5173"] # JSON array format
```

### CORS Configuration

**Format**: JSON array of allowed origin URLs

**Development**:
```bash
BACKEND_CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]
```

**Production** (add ALL frontend domains):
```bash
BACKEND_CORS_ORIGINS=["https://app.yourdomain.com", "https://www.yourdomain.com"]
```

**Common Issues**:
- [-] `BACKEND_CORS_ORIGINS=*` - Don't use wildcard in production (security risk)
- [-] `BACKEND_CORS_ORIGINS=http://localhost:5173` - Missing array brackets
- [-] Missing `https://` protocol - Must include protocol
- [X] `BACKEND_CORS_ORIGINS=["http://localhost:5173"]` - Correct format

**Testing CORS**:
```bash
# Should succeed if CORS configured
curl -X OPTIONS http://localhost:8000/api/v1/users \
 -H "Origin: http://localhost:5173" \
 -H "Access-Control-Request-Method: GET"
```

## Claude Code Skills

Use skills with `/skill-name` format:
- `/fastapi-endpoint` - Generate endpoints with dependencies
- `/fastapi-model` - Create PostgreSQL/MongoDB models
- `/fastapi-permission` - Add RBAC permissions
- `/fastapi-migration` - Alembic migrations
- `/fastapi-test` - Generate test files
- `/feature-from-plan` - Execute structured Claude.ai Project plan

**IMPORTANT**: Always invoke relevant skill when creating features - they contain boilerplate-specific patterns.

---

## Code Standards: MANDATORY for All Files

**CRITICAL**: Every Python file MUST start with Google-style docstring:
```python
"""Module description.

Detailed explanation of what this module does, its purpose in the application,
and any important patterns or conventions it follows.
"""
```

**Applies to**: app/, tests/, scripts/, migrations/ - NO EXCEPTIONS.

**When creating files**: Add docstring BEFORE any imports or code.

---

## Database Strategy: Choose Before Creating Models

<database_decision>
**PostgreSQL** (app/models/postgres/) - MUST use for:
- User authentication, relational data, foreign keys, ACID transactions, complex joins

**MongoDB** (app/models/mongodb/) - Use for:
- Flexible schemas, high-write workloads, nested documents, varying structures
</database_decision>

**Example**: Items → PostgreSQL (has `owner_id` FK to Users)

---

## Adding Feature: 7-Step Workflow

**1. Model** → Use `/fastapi-model` skill
- PostgreSQL: `app/models/postgres/your_model.py` with `Base`, ForeignKeys
- MongoDB: `app/models/mongodb/your_doc.py` with `Document`, MUST set `Settings.name`
- **MUST**: Start file with docstring describing model purpose

**2. Migration** (PostgreSQL only) → Use `/fastapi-migration` skill
```bash
uv run alembic revision --autogenerate -m "add table"
# IMPORTANT: Review alembic/versions/ before applying
uv run alembic upgrade head
```

**3. Schema** → `app/schemas/your_schema.py`
- MUST set `from_attributes = True` in Config for SQLAlchemy responses
- MongoDB ObjectId → use `str` type in schemas
- **MUST**: Docstring explaining schema's role

**4. Repository** → `app/repositories/your_repository.py`
```python
# PostgreSQL: Extend BaseRepository[YourModel]
# MongoDB: Create async methods (insert, find_one, etc.)
```
- **MUST**: Docstring describing data access patterns

**5. Service** → `app/services/your_service.py`
- Business logic, orchestrates repositories
- Password hashing happens here, NOT in models
- **MUST**: Docstring explaining business logic

**6. Endpoint** → Use `/fastapi-endpoint` skill
```python
# app/api/v1/your_endpoint.py
"""API endpoints for YourResource management."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.your_schema import CreateSchema, ResponseSchema

router = APIRouter()

@router.post("/", response_model=ResponseSchema)
def create(
 data: CreateSchema,
 db: Session = Depends(get_db), # MUST come before get_current_user
 current_user: User = Depends(get_current_user)
):
 # Instantiate repo → service → return
```
- **MUST**: Module docstring at top, describing API endpoints

**7. Register** → Add to `app/api/v1/router.py`

---

## RBAC: Add Permissions (Use /fastapi-permission skill)

1. Add to `app/common/permissions.py`:
```python
class Permission(str, Enum):
 YOUR_RESOURCE_CREATE = "your_resource:create"
```

2. Map to roles in `ROLE_PERMISSIONS`

3. Protect endpoint:
```python
@router.post("/", dependencies=[Depends(require_permissions(Permission.YOUR_RESOURCE_CREATE))])
```

**IMPORTANT**: Permission checks at API layer only, never in services.

---

## Testing (Use /fastapi-test skill)

**ALWAYS run in this order:**
```bash
uv run ruff format app tests
uv run ruff check --fix app tests
uv run mypy app
uv run pytest tests/unit -v
uv run pytest tests/integration -v
```

Test structure: `tests/unit/services/test_your_service.py`
```python
"""Tests for YourService business logic.""" # MUST have docstring

@pytest.fixture
def service(db_session):
 repo = YourRepository(db_session)
 return YourService(repo)

def test_create(service):
 result = service.create(YourModelCreate(name="test"))
 assert result.name == "test"
```

---

## Critical Gotchas

**Code Quality**
- Missing docstring → Ruff will fail, commit will be blocked
- Docstrings MUST be first thing in file (before imports)

**Database**
- MongoDB: MUST call `await init_beanie()` in `app/db/mongodb.py` for new documents
- Alembic: MUST import models in `alembic/env.py` or autogeneration fails
- Never commit migrations without reviewing generated SQL

**Dependencies**
- `get_db()` → SQLAlchemy session (PostgreSQL only)
- `get_current_user()` queries PostgreSQL - skip in MongoDB-only endpoints
- Dependency order: `get_current_user` MUST come after `get_db`

**Schemas**
- Forget `from_attributes = True` → Pydantic validation error
- MongoDB ObjectId as `ObjectId` type → serialization error (use `str`)
- Schema field mismatch → check model field names exactly

**Security**
- Hash passwords in services with `security.get_password_hash()`, NOT models
- Refresh tokens MUST be single-use (invalidate after use)
- 401 errors → verify `Authorization: Bearer <token>` header format

**Common Errors**
- "Table already exists" → `alembic downgrade -1` then `upgrade head`
- "Document not found" → check `Settings.name` matches collection
- Circular imports → move imports inside functions or use `TYPE_CHECKING`
- Type errors → run `mypy app` before committing

**Environment**
- Missing `.env` → copy from `.env.example`
- Wrong DB URLs → check `DATABASE_URL` and `MONGODB_URL` in `.env`
- Port conflicts → ensure 8000, 5432, 27017 available

---

## Dev Tools
```bash
docker compose --profile tools up -d # PgAdmin + Mongo Express
```
- PgAdmin: http://localhost:5050 (admin@admin.com / admin)
- Mongo Express: http://localhost:8081
- API Docs: http://localhost:8000/docs
