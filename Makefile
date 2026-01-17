# =============================================================================
# Makefile - FastAPI Boilerplate Development Commands
# =============================================================================

.PHONY: help
help: ## Show available commands
	@echo "FastAPI Boilerplate - Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# =============================================================================
# Setup & Installation
# =============================================================================

.PHONY: install
install: ## Install dependencies with UV
	uv sync

.PHONY: install-dev
install-dev: ## Install development dependencies
	uv sync --dev

.PHONY: update
update: ## Update dependencies
	uv lock --upgrade
	uv sync

# =============================================================================
# Database (Alembic)
# =============================================================================

.PHONY: db-migrate
db-migrate: ## Create new Alembic migration
	@read -p "Migration name: " name; \
	uv run alembic revision --autogenerate -m "$$name"

.PHONY: db-upgrade
db-upgrade: ## Apply pending migrations
	uv run alembic upgrade head

.PHONY: db-downgrade
db-downgrade: ## Revert last migration
	uv run alembic downgrade -1

.PHONY: db-reset
db-reset: ## Reset database (WARNING: Deletes all data!)
	@echo "WARNING: This will delete all data!"
	@read -p "Are you sure? [y/N] " confirm; \
	if [ "$$confirm" = "y" ]; then \
		uv run alembic downgrade base; \
		uv run alembic upgrade head; \
	fi

.PHONY: db-init
db-init: ## Initialize database with seed data
	uv run python scripts/init_db.py

# =============================================================================
# Development
# =============================================================================

.PHONY: dev
dev: ## Run development server
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

.PHONY: shell
shell: ## Open Python shell with project context
	uv run ipython

# =============================================================================
# Code Quality
# =============================================================================

.PHONY: format
format: ## Format code with Ruff
	uv run ruff format app tests
	uv run ruff check --fix app tests

.PHONY: lint
lint: ## Check code with Ruff
	uv run ruff check app tests

.PHONY: type-check
type-check: ## Check types with MyPy
	uv run mypy app

.PHONY: check
check: lint type-check ## Run all quality checks

# =============================================================================
# Testing
# =============================================================================

.PHONY: test
test: ## Run all tests
	uv run pytest

.PHONY: test-unit
test-unit: ## Run unit tests only
	uv run pytest tests/unit -v

.PHONY: test-integration
test-integration: ## Run integration tests
	uv run pytest tests/integration -v

.PHONY: test-cov
test-cov: ## Run tests with coverage report
	uv run pytest --cov=app --cov-report=html --cov-report=term

# =============================================================================
# Docker
# =============================================================================

.PHONY: docker-up
docker-up: ## Start development containers
	docker-compose up -d

.PHONY: docker-down
docker-down: ## Stop containers
	docker-compose down

.PHONY: docker-logs
docker-logs: ## View container logs
	docker-compose logs -f

.PHONY: docker-build
docker-build: ## Build Docker image
	docker-compose build

.PHONY: docker-clean
docker-clean: ## Clean containers and volumes
	docker-compose down -v
	docker system prune -f

.PHONY: docker-shell
docker-shell: ## Open shell in API container
	docker-compose exec api bash

.PHONY: docker-db-shell
docker-db-shell: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U app_user -d app_db

.PHONY: docker-tools
docker-tools: ## Start with PgAdmin & Mongo Express
	docker-compose --profile tools up -d

# =============================================================================
# Security
# =============================================================================

.PHONY: generate-secret
generate-secret: ## Generate JWT secret key
	@python -c "import secrets; print(secrets.token_hex(32))"

# =============================================================================
# Clean
# =============================================================================

.PHONY: clean
clean: ## Clean temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true

# =============================================================================
# Quick Start
# =============================================================================

.PHONY: setup
setup: install docker-up db-upgrade ## Complete project setup
	@echo "Project configured successfully!"
	@echo "Run 'make dev' to start the development server"

.PHONY: reset
reset: clean docker-clean setup ## Reset entire environment
	@echo "Environment reset complete"
