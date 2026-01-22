"""
Pydantic schemas (DTOs) for API request/response validation.

Provides data transfer objects that define the structure of API requests
and responses, with automatic validation, serialization, and documentation.

Key components:
    - User schemas: UserCreate, UserUpdate, UserResponse, UserListResponse
    - Item schemas: ItemCreate, ItemUpdate, ItemResponse, ItemListResponse
    - Auth schemas: LoginRequest, Token, RefreshTokenRequest

Dependencies:
    - pydantic: Data validation and serialization
    - email-validator: Email validation

Related files:
    - app/models/: Database models these schemas map to/from
    - app/api/v1/: Endpoints using these schemas
    - app/services/: Services using these for input validation

Common commands:
    - View schema docs: http://localhost:8000/docs (Swagger UI)

Example:
    Import schemas::

        from app.schemas import UserCreate, UserResponse
        from app.schemas.auth import LoginRequest, Token

    Using with FastAPI::

        @router.post("/users", response_model=UserResponse)
        async def create_user(user_data: UserCreate):
            # user_data is validated automatically
            ...

Schema naming convention:
    - {Resource}Base: Common fields shared across schemas
    - {Resource}Create: Request body for POST endpoints
    - {Resource}Update: Request body for PATCH endpoints (all optional)
    - {Resource}Response: Response body for single resource
    - {Resource}ListResponse: Response body for paginated lists
"""
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserPasswordUpdate,
    UserResponse,
    UserListResponse,
)
from app.schemas.item import (
    ItemBase,
    ItemCreate,
    ItemUpdate,
    ItemResponse,
    ItemListResponse,
)
from app.schemas.auth import (
    Token,
    TokenPayload,
    LoginRequest,
    RefreshTokenRequest,
)

__all__ = [
    # User schemas
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserPasswordUpdate",
    "UserResponse",
    "UserListResponse",
    # Item schemas
    "ItemBase",
    "ItemCreate",
    "ItemUpdate",
    "ItemResponse",
    "ItemListResponse",
    # Auth schemas
    "Token",
    "TokenPayload",
    "LoginRequest",
    "RefreshTokenRequest",
]
