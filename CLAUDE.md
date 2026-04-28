# CLAUDE.md - FastAPI Boilerplate with PostgreSQL + MongoDB

## Quick Start
```bash
uv sync && cp .env.example .env
uv run pre-commit install        # ONE-TIME — wires ruff lint + format + hygiene checks into git commits
docker compose up -d postgres mongodb
uv run alembic upgrade head
uv run python scripts/init_db.py # Creates admin@example.com / admin123
uv run dev                       # http://localhost:8000
```

> **Pre-commit**: must be installed once per clone with `uv run pre-commit install`. After that every `git commit` runs Ruff (lint + autofix + format) and basic file hygiene against staged files. Run on the whole tree manually with `uv run pre-commit run --all-files`. Tests and mypy are NOT in pre-commit by design — run those on demand (`uv run pytest`, `uv run mypy app`).

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

## Database Strategy

PostgreSQL is the default for relational, transactional, RBAC-bound data; MongoDB is reserved for flexible-schema and high-write payloads. The full decision tree (when to pick which, with examples beyond `Item`) lives in `../docs/ARCHITECTURE.md` § *Dual Database Strategy*; the canonical reference implementation is `app/models/postgres/item.py` (FK to `users.id`, `owner_id`-scoped queries in `app/repositories/item_repo.py`).

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
# app/api/v1/your_resource.py
"""API endpoints for YourResource management."""

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, YourResourceSvc
from app.schemas.your_resource import CreateSchema, ResponseSchema

router = APIRouter(prefix="/your-resource", tags=["your-resource"])


@router.post("/", response_model=ResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_resource(
    data: CreateSchema,
    current_user: CurrentUser,    # Annotated[User, Depends(get_current_active_user)]
    service: YourResourceSvc,     # Annotated[YourResourceService, Depends(get_your_resource_service)]
):
    return await service.create(data, current_user)
```
- **MUST**: Module docstring at top, describing API endpoints
- Use the `Annotated` type aliases exported from `app/api/deps.py` (`CurrentUser`, `CurrentAdmin`, `ItemSvc`, `UserSvc`, `UserRepo`, `ItemRepo`, `BlacklistRepo`). Don't write `Depends(get_db)` at the endpoint signature — repositories/services receive the `AsyncSession` internally.
- Endpoints must be `async def`; the entire stack is SQLAlchemy 2.0 async.

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
- Canonical injection lives in `app/api/deps.py` as `Annotated` type aliases (`CurrentUser`, `CurrentAdmin`, `ItemSvc`, `UserSvc`, `AuthSvc`, `UserRepo`, `ItemRepo`, `BlacklistRepo`). Endpoints declare them by annotation — no manual `Depends(...)` calls in route signatures.
- `get_db()` lives in `app/db/postgres.py` and yields an `AsyncSession`. Only repository/service factories consume it directly.
- `get_current_user` (cookie or `Authorization: Bearer`) lives in `app/api/deps.py`. Use `CurrentUser` for auth-required endpoints, `CurrentAdmin` for admin-only — both go through `get_current_active_user`.

**Schemas**
- Response schemas that wrap a SQLAlchemy row need Pydantic v2 `model_config = ConfigDict(from_attributes=True)` — see `app/schemas/user.py:142` and `app/schemas/item.py:96` for the canonical pattern. Without it, Pydantic refuses to read attribute-style ORM objects.
- MongoDB ObjectId in schemas → declare as `str`, not `bson.ObjectId` (which doesn't serialize cleanly to JSON).
- Schema field mismatch → field names must match the model exactly; SQLAlchemy column names ≠ Pydantic aliases.

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

## Multi-tenancy Status: NOT IMPLEMENTED

This boilerplate does **not** ship an `Organization` (tenant) model.

- `Item` is owned per-user via `owner_id` (FK to `users.id`) — see `app/models/postgres/item.py:85` and `app/repositories/item_repo.py:66-98`.
- The comment in `app/models/postgres/user.py:74` ("organization_id: For multi-tenant applications") is aspirational; no column exists.

**Policy until `Organization` is introduced**:
- Every query that returns user-scoped data MUST filter by `owner_id`. Cross-user reads are a security bug.
- When introducing `Organization`, every domain model gets `organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), index=True)` and every query also filters by it. Add a regression test before the refactor.

**See**: `../docs/audits/claude-setup-audit-2026-04-25.md` (CRITICAL-1) and `../.claude/rules/backend-data-layer.md`.

---

## Dev Tools
```bash
docker compose --profile tools up -d # PgAdmin + Mongo Express
```
- PgAdmin: http://localhost:5050 (admin@admin.com / admin)
- Mongo Express: http://localhost:8081
- API Docs: http://localhost:8000/docs

---

## Project-level docs (super-repo)

When the backend is mounted as a submodule of `saas-boilerplate`, additional cross-cutting docs live one level up:

- `../.claude/scratch/{audits,plans}/` — gitignored ephemeral. Meta-audits + tactical plans about the Claude setup. Borrar libre.
- `../docs/plans/active/` — committed. Multi-day feature plans worth tracking while in flight.
- `../docs/adr/` — committed. Permanent architectural decisions (e.g. `001-dual-database-strategy.md`).
- `../docs/gotchas.md` — running log of real incidents.
- `../.claude/rules/backend-data-layer.md` — repository/service rules + multi-tenancy gap reminder.
- `../.claude/rules/backend-migrations.md` — Alembic autogenerate-only workflow.

_Archive_: `../docs/audits/` and `../docs/plans/` (root) hold pre-2026-04-28 work. Read-only history.
