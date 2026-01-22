"""
Business logic services implementing the Service Layer pattern.

Contains all business logic, orchestrates operations across repositories,
enforces business rules, and handles authorization checks.

Key components:
    - AuthService: Authentication (login, token refresh, validation)
    - UserService: User management (CRUD, password, roles)
    - ItemService: Item management (CRUD with ownership)

Dependencies:
    - app.repositories: Data access layer
    - app.common.exceptions: Business error types
    - app.common.security: Security utilities
    - app.common.permissions: RBAC utilities

Related files:
    - app/api/v1/: API endpoints that use these services
    - app/api/deps.py: Dependency injection for services
    - app/repositories/: Data access layer

Common commands:
    - Test: uv run pytest tests/ -v

Example:
    Import services::

        from app.services import AuthService, UserService, ItemService

    Creating a new service::

        from app.repositories.product_repo import ProductRepository

        class ProductService:
            def __init__(self, product_repo: ProductRepository):
                self.product_repo = product_repo

            async def get_product(self, product_id: UUID) -> Product:
                product = await self.product_repo.get(product_id)
                if not product:
                    raise NotFoundError(...)
                return product

Service Layer responsibilities:
    - Business rule enforcement
    - Authorization checks
    - Coordinating multiple repositories
    - Raising appropriate business exceptions
    - NOT handling HTTP concerns (that's the API layer)
"""
from app.services.user_service import UserService
from app.services.auth_service import AuthService
from app.services.item_service import ItemService

__all__ = [
    "UserService",
    "AuthService",
    "ItemService",
]
