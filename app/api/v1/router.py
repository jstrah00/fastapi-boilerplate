"""
API v1 router that combines all endpoint routers.

Central router that aggregates all v1 API endpoint routers into a single
router that's mounted on the application with the /api/v1 prefix.

Key components:
    - api_router: Main APIRouter instance combining all sub-routers
    - auth: Authentication endpoints (/auth/login, /auth/refresh, /auth/logout)
    - users: User management endpoints (/users/*)
    - items: Item CRUD endpoints (/items/*)

Dependencies:
    - fastapi: APIRouter
    - app.api.v1.auth: Authentication router
    - app.api.v1.users: Users router
    - app.api.v1.items: Items router

Related files:
    - app/main.py: Mounts this router with API_V1_PREFIX
    - app/api/v1/auth.py: Auth endpoints
    - app/api/v1/users.py: User endpoints
    - app/api/v1/items.py: Item endpoints

Common commands:
    - View all routes: http://localhost:8000/docs

Example:
    Adding a new router::

        # 1. Create app/api/v1/products.py with router
        # 2. Import and include here:
        from app.api.v1 import products
        api_router.include_router(products.router)

    Full URL structure::

        /api/v1/auth/login      (POST)
        /api/v1/auth/refresh    (POST)
        /api/v1/users/          (GET, POST)
        /api/v1/users/me        (GET)
        /api/v1/users/{id}      (GET, PATCH, DELETE)
        /api/v1/items/          (GET, POST)
        /api/v1/items/{id}      (GET, PATCH, DELETE)
"""
from fastapi import APIRouter

from app.api.v1 import users, auth, items, chat

api_router = APIRouter()

# Include all routers
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(items.router)
api_router.include_router(chat.router)

# NOTE: Add more routers as you create them:
# api_router.include_router(my_resource.router)
