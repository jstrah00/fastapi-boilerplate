"""
API version 1 endpoints.

Contains all v1 API endpoint routers, organized by resource. Each router
handles a specific domain (auth, users, items) with full CRUD operations.

Key components:
    - router.py: Combines all routers into api_router
    - auth.py: Authentication endpoints (/auth/*)
    - users.py: User management endpoints (/users/*)
    - items.py: Item CRUD endpoints (/items/*)

Dependencies:
    - fastapi: APIRouter
    - app.services: Business logic
    - app.schemas: Request/response schemas

Related files:
    - app/api/v1/router.py: Main router combining all sub-routers
    - app/main.py: Mounts api_router with /api/v1 prefix

Common commands:
    - View docs: http://localhost:8000/docs
    - View ReDoc: http://localhost:8000/redoc

Example:
    Adding a new resource router::

        # 1. Create app/api/v1/products.py
        from fastapi import APIRouter
        router = APIRouter(prefix="/products", tags=["products"])

        @router.get("/")
        async def list_products():
            ...

        # 2. Register in app/api/v1/router.py
        from app.api.v1 import products
        api_router.include_router(products.router)
"""
