"""
API v1 router that combines all endpoint routers.

# =============================================================================
# ROUTER: Include all your API routers here.
# =============================================================================
"""
from fastapi import APIRouter

from app.api.v1 import users, auth, items

api_router = APIRouter()

# Include all routers
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(items.router)

# NOTE: Add more routers as you create them:
# api_router.include_router(my_resource.router)
