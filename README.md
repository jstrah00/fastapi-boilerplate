# Backend - FastAPI Service

Production-ready FastAPI backend with PostgreSQL + MongoDB support, designed for rapid SaaS development. This is a **Git submodule** of the SaaS Boilerplate monorepo.

**For complete setup instructions, see**: `../docs/GETTING_STARTED.md` in the root directory.

## About This Module

This backend service is designed to work as part of the SaaS Boilerplate monorepo but can also be used independently. It includes integrated Claude Code skills and workflow optimizations for AI-assisted development.

## Available Claude Code Skills

Use these skills to rapidly generate backend code following project conventions:

- `/fastapi-endpoint` - Generate complete CRUD endpoint with schema, repository, service, and router
- `/fastapi-model` - Create SQLAlchemy models with proper typing, relationships, and indexes
- `/fastapi-migration` - Create and manage Alembic database migrations
- `/fastapi-permission` - Add new permissions and roles to RBAC system
- `/fastapi-test` - Generate comprehensive unit and integration tests
- `/feature-from-plan` - Systematically implement features from structured Claude.ai Project prompts (two-stage workflow)

**See**: `CLAUDE.md` for detailed usage and patterns

## Features

- **FastAPI** with async support
- **Dual Database**: PostgreSQL + MongoDB (use one or both)
- **Authentication**: JWT with access/refresh tokens
- **Role-Based Permissions**: Flexible RBAC system
- **Repository Pattern**: Clean data access abstraction
- **Service Layer**: Business logic separation
- **Structured Logging**: JSON logs with structlog
- **Docker Compose**: Complete development environment
- **Alembic**: Database migrations for PostgreSQL
- **Testing**: Pytest with async support

## Quick Start

### Prerequisites

- Python 3.11+
- [UV](https://docs.astral.sh/uv/) (Python package manager) - [Install Guide](https://docs.astral.sh/uv/)
- Docker & Docker Compose

**Note**: If you cloned the monorepo, submodules are automatically set up. This setup is for standalone backend development only.

### Standalone Setup (Backend Only)

```bash
# If working standalone (not recommended - use monorepo instead)
cd backend

# Copy environment file
cp .env.example .env

# Install dependencies
uv sync

# Start databases
docker compose up -d postgres mongodb

# Run migrations
uv run alembic upgrade head

# Initialize database with admin user
uv run python scripts/init_db.py

# Start development server
uv run dev
```

The API will be available at `http://localhost:8000`.

### Default Admin Credentials

- **Email**: admin@example.com
- **Password**: admin123

**Change these immediately in production!**

## Project Structure

```
.
├── app/
│ ├── api/
│ │ ├── v1/ # API version 1 endpoints
│ │ │ ├── auth.py # Authentication endpoints
│ │ │ ├── users.py # User CRUD endpoints
│ │ │ └── items.py # Example CRUD endpoints
│ │ ├── deps.py # Dependency injection
│ │ └── handlers.py # Exception handlers
│ │
│ ├── common/
│ │ ├── exceptions.py # Custom exceptions
│ │ ├── logging.py # Structured logging
│ │ ├── permissions.py# Role-based access control
│ │ ├── security.py # JWT & password utils
│ │ └── alerts.py # Telegram alerts (optional)
│ │
│ ├── db/
│ │ ├── postgres.py # PostgreSQL connection
│ │ ├── mongodb.py # MongoDB connection
│ │ └── unit_of_work.py # Cross-DB transactions
│ │
│ ├── models/
│ │ ├── postgres/ # SQLAlchemy models
│ │ │ ├── user.py
│ │ │ └── item.py
│ │ └── mongodb/ # Beanie documents
│ │ └── document.py
│ │
│ ├── repositories/ # Data access layer
│ │ ├── base.py
│ │ ├── user_repo.py
│ │ └── item_repo.py
│ │
│ ├── schemas/ # Pydantic DTOs
│ │ ├── auth.py
│ │ ├── user.py
│ │ └── item.py
│ │
│ ├── services/ # Business logic
│ │ ├── auth_service.py
│ │ ├── user_service.py
│ │ └── item_service.py
│ │
│ ├── config.py # Application settings
│ └── main.py # Application entry point
│
├── alembic/ # Database migrations
├── scripts/ # Initialization scripts
├── tests/ # Test suite
├── docker-compose.yml # Development containers
└── pyproject.toml # Project configuration
```


## Feature Development Workflow (Optional - For Claude Code Users)

This boilerplate includes a two-stage workflow for implementing new features efficiently with Claude Code:

1. **Planning Stage** (Claude.ai Project): Define features with business context
2. **Implementation Stage** (Claude Code): Execute with optimized, pattern-aware prompts

**Benefits:**
- Reduces Claude Code token usage (important for Pro plan limits)
- Ensures features follow boilerplate conventions automatically
- Generates production-ready code faster
- Maintains architectural consistency

**Note:** This workflow is designed specifically for Claude Code users and is completely optional. You can develop features using your preferred method - the workflow simply provides optimized patterns if you choose to use Claude Code.

**Read the complete guide:** [docs/FEATURE_WORKFLOW.md](docs/FEATURE_WORKFLOW.md)

### Quick Start

1. One-time setup: Create Claude.ai Project ([Setup Guide](docs/FEATURE_WORKFLOW.md#one-time-setup))
2. Describe your feature in the Project
3. Get an optimized Claude Code prompt
4. Run in Claude Code using plan mode
5. Ship

**Example:**
```
Claude.ai Project: "Add user subscription tiers with Stripe"
 ↓
Generated Prompt (copied to Claude Code)
 ↓
Claude Code: Uses plan mode, implements following boilerplate patterns
 ↓
Production-ready code
```

## Available Commands

### Docker Commands

```bash
# Start databases (PostgreSQL + MongoDB)
docker compose up -d postgres mongodb

# Start all services (including API in container)
docker compose up -d

# Start with development tools (PgAdmin + Mongo Express)
docker compose --profile tools up -d

# Stop all containers
docker compose down

# Stop and remove volumes (WARNING: deletes data)
docker compose down -v

# View logs
docker compose logs -f
docker compose logs -f postgres # Specific service

# Database shells
docker compose exec postgres psql -U app_user -d app_db
docker compose exec mongodb mongosh -u app_admin -p app_mongo_password
```

### Python/uv Commands

```bash
# Install dependencies
uv sync

# Start development server
uv run dev

# Open Python shell
uv run ipython
```

### Database Migrations (Alembic)

```bash
# Apply all pending migrations
uv run alembic upgrade head

# Create new migration
uv run alembic revision --autogenerate -m "migration description"

# Revert last migration
uv run alembic downgrade -1

# Reset database (revert all + apply all)
uv run alembic downgrade base && uv run alembic upgrade head

# Initialize with seed data (admin user)
uv run python scripts/init_db.py
```

### Code Quality

```bash
# Format code
uv run ruff format app tests
uv run ruff check --fix app tests

# Lint code
uv run ruff check app tests

# Type checking
uv run mypy app

# Run all quality checks
uv run ruff check app tests && uv run mypy app
```

### Testing

```bash
# Run all tests with coverage (uses uv script)
uv run test

# Run all tests (without coverage)
uv run pytest

# Run specific tests
uv run pytest tests/unit -v
uv run pytest tests/integration -v
```

### Utilities

```bash
# Generate secret key
python -c "import secrets; print(secrets.token_hex(32))"

# Clean temporary files
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null
find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null
find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null
find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null
```

## Configuration

All configuration is done via environment variables. See `.env.example` for all options.

### Database Options

This boilerplate supports both PostgreSQL and MongoDB. You can use:

1. **Both databases** (default): Use PostgreSQL for structured data and MongoDB for flexible documents
2. **PostgreSQL only**: Remove MongoDB-related code (see comments in code)
3. **MongoDB only**: Remove PostgreSQL-related code (see comments in code)

### Role-Based Permissions

The permission system is defined in `app/common/permissions.py`:

```python
# Define permissions
class Permission(str, Enum):
 USERS_READ = "users:read"
 USERS_CREATE = "users:create"
 # Add more...

# Define roles with permission sets
ROLE_PERMISSIONS = {
 Role.ADMIN: {Permission.USERS_READ, Permission.USERS_CREATE, ...},
 Role.USER: {Permission.ITEMS_READ, ...},
}

# Use in endpoints
@router.get("/admin/users")
async def admin_list_users(
 current_user: User = Depends(require_permissions(Permission.USERS_READ))
):
 ...
```

## API Documentation

Once running, access the API docs at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Development Tools

Start with optional tools (PgAdmin & Mongo Express):

```bash
docker compose --profile tools up -d
```

- **PgAdmin**: http://localhost:5050 (admin@local.dev / admin)
- **Mongo Express**: http://localhost:8081 (admin / admin)

## Testing

```bash
# Run all tests with coverage
uv run test

# Run specific tests
uv run pytest tests/unit -v
uv run pytest tests/integration -v
```

## Deployment

### Production Checklist

1. Change `SECRET_KEY` (use `python -c "import secrets; print(secrets.token_hex(32))"`)
2. Set `DEBUG=false`
3. Set `ENVIRONMENT=production`
4. Update CORS origins
5. Change default admin password
6. Configure proper database credentials
7. Set up Telegram alerts (optional)

### Docker Production

```bash
# Build production image
docker build -f Dockerfile -t your-app:latest .

# Run with production settings
docker run -e ENVIRONMENT=production your-app:latest
```

## Customization Guide

### Adding a New Model (PostgreSQL)

1. Create model in `app/models/postgres/your_model.py`
2. Import in `alembic/env.py`
3. Create migration: `uv run alembic revision --autogenerate -m "add your_model"`
4. Apply migration: `uv run alembic upgrade head`

### Adding a New Model (MongoDB)

1. Create document in `app/models/mongodb/your_document.py`
2. Register in `app/db/mongodb.py` `init_mongodb()` function

### Adding a New API Endpoint

1. Create schema in `app/schemas/`
2. Create repository in `app/repositories/`
3. Create service in `app/services/`
4. Create router in `app/api/v1/`
5. Register router in `app/api/v1/router.py`
6. Add dependencies in `app/api/deps.py`

### Adding New Permissions

1. Add permission to `Permission` enum in `app/common/permissions.py`
2. Add permission to relevant roles in `ROLE_PERMISSIONS`
3. Use `require_permissions()` in your endpoints

## License

MIT License - feel free to use this boilerplate for any project.
