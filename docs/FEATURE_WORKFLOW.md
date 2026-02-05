# Backend Feature Development Workflow

Step-by-step guide for implementing features in this FastAPI backend with PostgreSQL + MongoDB.

## Table of Contents
- [Quick Start](#quick-start)
- [Feature Implementation Flow](#feature-implementation-flow)
- [Common Feature Types](#common-feature-types)
- [Integration with Frontend](#integration-with-frontend)
- [Testing Strategy](#testing-strategy)
- [Tips & Best Practices](#tips--best-practices)

---

## Quick Start

### Prerequisites
- Docker services running (PostgreSQL, MongoDB)
- Backend running at http://localhost:8000
- Familiarity with FastAPI, SQLAlchemy, and async Python
- Python 3.11+ with UV package manager

### Typical Feature Timeline
- Simple CRUD: 1-2 hours
- Form with validation: 30-45 minutes
- Complex business logic: 2-4 hours
- Multi-database feature: 3-5 hours

---

## Feature Implementation Flow

### Step 1: Choose Database (Critical Decision)

**This decision affects the entire implementation!**

#### Use PostgreSQL for:
- [X] User management (authentication, profiles)
- [X] Roles & permissions (RBAC)
- [X] Transactional data requiring ACID guarantees
- [X] Complex relationships (foreign keys, joins)
- [X] Data with strict schema requirements
- [X] Billing and payment data

#### Use MongoDB for:
- [X] Event logs & audit trails
- [X] Analytics data & metrics
- [X] Flexible schemas (varying structure)
- [X] High write throughput
- [X] Nested/hierarchical data
- [X] Temporary/cached data

**Example**: For a product catalog with categories and pricing, use PostgreSQL (structured data with relationships).

---

### Step 2: Define Models

#### PostgreSQL Model

Create model in `backend/app/models/postgres/`:

```python
"""Product model for inventory management.

This module defines the Product SQLAlchemy model representing products in the catalog.
Includes relationships to categories and pricing tiers.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Product(Base):
 """Product model representing items in the catalog.

 Attributes:
 id: Unique product identifier
 name: Product name (max 200 chars)
 description: Optional product description
 sku: Stock Keeping Unit (unique identifier)
 price: Product price (Decimal for precision)
 stock_quantity: Current inventory count
 category_id: Foreign key to Category
 is_active: Soft delete flag
 created_at: Timestamp of creation
 updated_at: Timestamp of last update
 """

 __tablename__ = "products"

 id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
 name: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
 description: Mapped[str | None] = mapped_column(String, nullable=True)
 sku: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
 price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
 stock_quantity: Mapped[int] = mapped_column(default=0, nullable=False)
 category_id: Mapped[UUID] = mapped_column(ForeignKey("categories.id"), nullable=False)
 is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
 created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
 updated_at: Mapped[datetime] = mapped_column(
 DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
 )

 # Relationships
 category: Mapped["Category"] = relationship("Category", back_populates="products")
```

**Key Points**:
- Always add module docstring describing purpose
- Use type hints with `Mapped[]`
- Index frequently queried fields
- Use `Decimal` for money (not `float`)
- Include `created_at` and `updated_at` timestamps
- Soft delete with `is_active` flag

#### MongoDB Document

Create document model in `backend/app/models/mongodb/`:

```python
"""Event log document for tracking user actions.

This module defines the EventLog document for storing application events
in MongoDB with flexible schema for metadata.
"""

from datetime import datetime
from typing import Any

from beanie import Document
from pydantic import Field


class EventLog(Document):
 """Event log document for tracking application events.

 Attributes:
 event_type: Type of event (e.g., 'user_login', 'product_created')
 user_id: UUID of user who triggered event
 timestamp: When the event occurred
 metadata: Flexible dict for event-specific data
 """

 event_type: str = Field(..., description="Type of event")
 user_id: str = Field(..., description="User who triggered the event")
 timestamp: datetime = Field(default_factory=datetime.utcnow)
 metadata: dict[str, Any] = Field(default_factory=dict, description="Flexible event data")

 class Settings:
 name = "event_logs" # Collection name
 indexes = [
 "event_type",
 "user_id",
 "timestamp",
 ]
```

**Key Points**:
- Inherit from `beanie.Document`
- Must set `Settings.name` to collection name
- Define indexes in `Settings.indexes`
- Use flexible types (`dict[str, Any]`) for varying structures
- Always add module and class docstrings

---

### Step 3: Create Migration (PostgreSQL only)

**Alembic manages PostgreSQL schema changes:**

```bash
# Auto-generate migration from model changes
cd backend
uv run alembic revision --autogenerate -m "add products table"

# Review generated migration in alembic/versions/
# IMPORTANT: Always review before applying!

# Apply migration
uv run alembic upgrade head

# Verify current migration
uv run alembic current
```

**Critical**:
- ALWAYS review generated migrations before applying
- Check that down migration (rollback) is correct
- Verify foreign key constraints are created
- Ensure indexes are included

**MongoDB**: No migrations needed - schema is flexible.

---

### Step 4: Define Schemas

Create Pydantic schemas in `backend/app/schemas/`:

```python
"""Product schemas for request/response validation.

This module defines Pydantic schemas for Product API endpoints,
handling validation and serialization.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
 """Base product schema with common fields."""

 name: str = Field(..., min_length=2, max_length=200, description="Product name")
 description: str | None = Field(None, description="Optional product description")
 sku: str = Field(..., min_length=1, max_length=50, description="Stock Keeping Unit")
 price: Decimal = Field(..., gt=0, description="Product price (must be positive)")
 stock_quantity: int = Field(..., ge=0, description="Current inventory count")
 category_id: UUID = Field(..., description="Category UUID")


class ProductCreate(ProductBase):
 """Schema for creating a new product."""

 pass # Inherits all fields from ProductBase


class ProductUpdate(ProductBase):
 """Schema for updating an existing product (all fields optional)."""

 name: str | None = Field(None, min_length=2, max_length=200)
 description: str | None = None
 sku: str | None = Field(None, min_length=1, max_length=50)
 price: Decimal | None = Field(None, gt=0)
 stock_quantity: int | None = Field(None, ge=0)
 category_id: UUID | None = None


class ProductResponse(ProductBase):
 """Schema for product responses (includes DB fields)."""

 model_config = ConfigDict(from_attributes=True) # Allow ORM objects

 id: UUID
 is_active: bool
 created_at: datetime
 updated_at: datetime
```

**Key Points**:
- `ProductBase` contains common fields
- `ProductCreate` for POST requests
- `ProductUpdate` for PUT/PATCH (fields optional)
- `ProductResponse` for API responses (includes `id`, timestamps)
- Set `from_attributes = True` to serialize SQLAlchemy models
- Use `Field()` with validation (min_length, gt, ge, etc.)

---

### Step 5: Repository Layer

Create repository in `backend/app/repositories/`:

```python
"""Product repository for database operations.

This module provides data access methods for the Product model,
implementing the repository pattern to abstract database queries.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.postgres.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


class ProductRepository:
 """Repository for Product database operations.

 Handles all database queries for products, providing a clean
 interface for the service layer.
 """

 def __init__(self, session: AsyncSession):
 """Initialize repository with database session.

 Args:
 session: SQLAlchemy async session
 """
 self.session = session

 async def get_by_id(self, product_id: UUID) -> Product | None:
 """Fetch product by ID.

 Args:
 product_id: UUID of the product

 Returns:
 Product if found, None otherwise
 """
 result = await self.session.execute(
 select(Product).where(Product.id == product_id)
 )
 return result.scalar_one_or_none()

 async def get_all(
 self, skip: int = 0, limit: int = 100, category_id: UUID | None = None
 ) -> list[Product]:
 """Fetch all products with pagination and optional filtering.

 Args:
 skip: Number of records to skip (pagination)
 limit: Maximum number of records to return
 category_id: Optional category filter

 Returns:
 List of products
 """
 query = select(Product).where(Product.is_active == True)

 if category_id:
 query = query.where(Product.category_id == category_id)

 query = query.offset(skip).limit(limit)

 result = await self.session.execute(query)
 return list(result.scalars().all())

 async def create(self, product_data: ProductCreate) -> Product:
 """Create a new product.

 Args:
 product_data: Product creation schema

 Returns:
 Created product with generated ID
 """
 product = Product(**product_data.model_dump())
 self.session.add(product)
 await self.session.commit()
 await self.session.refresh(product)
 return product

 async def update(self, product: Product, product_data: ProductUpdate) -> Product:
 """Update an existing product.

 Args:
 product: Product instance to update
 product_data: Update data (only provided fields are updated)

 Returns:
 Updated product
 """
 update_data = product_data.model_dump(exclude_unset=True)
 for field, value in update_data.items():
 setattr(product, field, value)

 await self.session.commit()
 await self.session.refresh(product)
 return product

 async def delete(self, product: Product) -> None:
 """Soft delete a product (set is_active = False).

 Args:
 product: Product to delete
 """
 product.is_active = False
 await self.session.commit()
```

**Key Points**:
- Repository handles all database queries
- Constructor takes `AsyncSession`
- Use `async`/`await` for all database operations
- Soft delete (set `is_active = False`) instead of hard delete
- Use `model_dump(exclude_unset=True)` for partial updates

---

### Step 6: Service Layer

Create service in `backend/app/services/`:

```python
"""Product service for business logic.

This module contains business logic for product management,
orchestrating repository calls and applying domain rules.
"""

from uuid import UUID

from app.common.exceptions import NotFoundException
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate


class ProductService:
 """Service for product business logic.

 Handles product operations with business rules and validations.
 """

 def __init__(self, repository: ProductRepository):
 """Initialize service with repository.

 Args:
 repository: Product repository instance
 """
 self.repository = repository

 async def get_product(self, product_id: UUID) -> ProductResponse:
 """Get product by ID.

 Args:
 product_id: UUID of the product

 Returns:
 Product response schema

 Raises:
 NotFoundException: If product not found
 """
 product = await self.repository.get_by_id(product_id)
 if not product or not product.is_active:
 raise NotFoundException(f"Product {product_id} not found")
 return ProductResponse.model_validate(product)

 async def get_products(
 self, skip: int = 0, limit: int = 100, category_id: UUID | None = None
 ) -> list[ProductResponse]:
 """Get all products with pagination.

 Args:
 skip: Records to skip
 limit: Max records to return
 category_id: Optional category filter

 Returns:
 List of product responses
 """
 products = await self.repository.get_all(skip, limit, category_id)
 return [ProductResponse.model_validate(p) for p in products]

 async def create_product(self, product_data: ProductCreate) -> ProductResponse:
 """Create a new product.

 Args:
 product_data: Product creation data

 Returns:
 Created product
 """
 # Business logic can go here (e.g., validate SKU format, check stock)
 product = await self.repository.create(product_data)
 return ProductResponse.model_validate(product)

 async def update_product(
 self, product_id: UUID, product_data: ProductUpdate
 ) -> ProductResponse:
 """Update an existing product.

 Args:
 product_id: UUID of product to update
 product_data: Update data

 Returns:
 Updated product

 Raises:
 NotFoundException: If product not found
 """
 product = await self.repository.get_by_id(product_id)
 if not product or not product.is_active:
 raise NotFoundException(f"Product {product_id} not found")

 updated_product = await self.repository.update(product, product_data)
 return ProductResponse.model_validate(updated_product)

 async def delete_product(self, product_id: UUID) -> None:
 """Delete a product (soft delete).

 Args:
 product_id: UUID of product to delete

 Raises:
 NotFoundException: If product not found
 """
 product = await self.repository.get_by_id(product_id)
 if not product or not product.is_active:
 raise NotFoundException(f"Product {product_id} not found")

 await self.repository.delete(product)
```

**Key Points**:
- Service contains business logic
- Orchestrates repository calls
- Converts ORM models to Pydantic schemas
- Raises exceptions for error cases
- Validates business rules (e.g., check stock before order)

---

### Step 7: API Endpoints

Create router in `backend/app/api/v1/endpoints/`:

```python
"""Product API endpoints.

This module defines REST API endpoints for product management,
including CRUD operations with proper authentication and permissions.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dependencies import get_current_user, get_db, require_permissions
from app.common.permissions import Permission
from app.models.postgres.user import User
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services.product_service import ProductService


router = APIRouter(prefix="/products", tags=["products"])


def get_product_service(db: AsyncSession = Depends(get_db)) -> ProductService:
 """Dependency to get ProductService instance.

 Args:
 db: Database session

 Returns:
 ProductService instance
 """
 repository = ProductRepository(db)
 return ProductService(repository)


@router.get("/", response_model=list[ProductResponse])
async def list_products(
 skip: int = Query(0, ge=0, description="Records to skip"),
 limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
 category_id: UUID | None = Query(None, description="Filter by category"),
 service: ProductService = Depends(get_product_service),
 current_user: User = Depends(require_permissions(Permission.PRODUCTS_READ)),
):
 """List all products with pagination.

 Args:
 skip: Number of records to skip (pagination)
 limit: Maximum records to return
 category_id: Optional category filter
 service: Product service dependency
 current_user: Authenticated user with PRODUCTS_READ permission

 Returns:
 List of products
 """
 return await service.get_products(skip, limit, category_id)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
 product_id: UUID,
 service: ProductService = Depends(get_product_service),
 current_user: User = Depends(require_permissions(Permission.PRODUCTS_READ)),
):
 """Get a single product by ID.

 Args:
 product_id: Product UUID
 service: Product service dependency
 current_user: Authenticated user with PRODUCTS_READ permission

 Returns:
 Product details

 Raises:
 HTTPException: 404 if product not found
 """
 return await service.get_product(product_id)


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
 product_data: ProductCreate,
 service: ProductService = Depends(get_product_service),
 current_user: User = Depends(require_permissions(Permission.PRODUCTS_WRITE)),
):
 """Create a new product.

 Args:
 product_data: Product creation data
 service: Product service dependency
 current_user: Authenticated user with PRODUCTS_WRITE permission

 Returns:
 Created product
 """
 return await service.create_product(product_data)


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
 product_id: UUID,
 product_data: ProductUpdate,
 service: ProductService = Depends(get_product_service),
 current_user: User = Depends(require_permissions(Permission.PRODUCTS_WRITE)),
):
 """Update an existing product.

 Args:
 product_id: Product UUID
 product_data: Update data (only provided fields are updated)
 service: Product service dependency
 current_user: Authenticated user with PRODUCTS_WRITE permission

 Returns:
 Updated product

 Raises:
 HTTPException: 404 if product not found
 """
 return await service.update_product(product_id, product_data)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
 product_id: UUID,
 service: ProductService = Depends(get_product_service),
 current_user: User = Depends(require_permissions(Permission.PRODUCTS_DELETE)),
):
 """Delete a product (soft delete).

 Args:
 product_id: Product UUID
 service: Product service dependency
 current_user: Authenticated user with PRODUCTS_DELETE permission

 Raises:
 HTTPException: 404 if product not found
 """
 await service.delete_product(product_id)
```

**Register Router** in `backend/app/api/v1/router.py`:
```python
from app.api.v1.endpoints import products

api_router = APIRouter()
api_router.include_router(products.router)
```

**Key Points**:
- Use `APIRouter` with prefix and tags
- Create dependency for service instantiation
- Use `Depends(require_permissions(...))` for auth
- Document all parameters with docstrings
- Use appropriate HTTP status codes (201 for creation, 204 for deletion)
- Pagination with `skip` and `limit` query params

---

### Step 8: Add Permissions

Add permissions to `backend/app/common/permissions.py`:

```python
class Permission(str, Enum):
 """Permission enumeration for RBAC."""

 # Existing permissions
 USERS_READ = "users:read"
 USERS_WRITE = "users:write"
 # ... other permissions

 # New product permissions
 PRODUCTS_READ = "products:read"
 PRODUCTS_WRITE = "products:write"
 PRODUCTS_DELETE = "products:delete"
```

**Create migration for permissions**:
```bash
uv run alembic revision -m "add product permissions"
```

**Manually add permissions in migration**:
```python
def upgrade():
 # Insert new permissions
 op.execute("""
 INSERT INTO permissions (name, description)
 VALUES
 ('products:read', 'View products'),
 ('products:write', 'Create and edit products'),
 ('products:delete', 'Delete products');
 """)

def downgrade():
 # Remove permissions
 op.execute("""
 DELETE FROM permissions
 WHERE name IN ('products:read', 'products:write', 'products:delete');
 """)
```

**Assign to roles**:
- Admin: All product permissions
- User: `PRODUCTS_READ` only

---

### Step 9: Write Tests

Create tests in `backend/tests/integration/`:

```python
"""Integration tests for product endpoints.

This module contains tests for product CRUD operations,
including authentication and permission checks.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.postgres.product import Product
from app.schemas.product import ProductCreate


@pytest.mark.asyncio
async def test_list_products(client: AsyncClient, auth_headers: dict):
 """Test listing products with pagination."""
 response = await client.get("/api/v1/products", headers=auth_headers)
 assert response.status_code == 200
 assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_create_product(client: AsyncClient, admin_headers: dict):
 """Test creating a new product (admin only)."""
 product_data = {
 "name": "Test Product",
 "description": "A test product",
 "sku": "TEST-001",
 "price": "29.99",
 "stock_quantity": 100,
 "category_id": "some-uuid-here",
 }

 response = await client.post(
 "/api/v1/products", json=product_data, headers=admin_headers
 )
 assert response.status_code == 201
 data = response.json()
 assert data["name"] == "Test Product"
 assert data["sku"] == "TEST-001"


@pytest.mark.asyncio
async def test_create_product_forbidden(client: AsyncClient, user_headers: dict):
 """Test that non-admin cannot create products."""
 product_data = {
 "name": "Test Product",
 "sku": "TEST-001",
 "price": "29.99",
 "stock_quantity": 100,
 "category_id": "some-uuid-here",
 }

 response = await client.post(
 "/api/v1/products", json=product_data, headers=user_headers
 )
 assert response.status_code == 403 # Forbidden


@pytest.mark.asyncio
async def test_update_product(
 client: AsyncClient, admin_headers: dict, db_session: AsyncSession
):
 """Test updating an existing product."""
 # Create test product
 product = Product(
 name="Original Name",
 sku="TEST-002",
 price=19.99,
 stock_quantity=50,
 category_id="some-uuid",
 )
 db_session.add(product)
 await db_session.commit()

 # Update product
 update_data = {"name": "Updated Name", "price": "24.99"}
 response = await client.patch(
 f"/api/v1/products/{product.id}", json=update_data, headers=admin_headers
 )

 assert response.status_code == 200
 data = response.json()
 assert data["name"] == "Updated Name"
 assert float(data["price"]) == 24.99


@pytest.mark.asyncio
async def test_delete_product(
 client: AsyncClient, admin_headers: dict, db_session: AsyncSession
):
 """Test deleting a product (soft delete)."""
 # Create test product
 product = Product(
 name="To Delete",
 sku="TEST-003",
 price=9.99,
 stock_quantity=10,
 category_id="some-uuid",
 )
 db_session.add(product)
 await db_session.commit()

 # Delete product
 response = await client.delete(
 f"/api/v1/products/{product.id}", headers=admin_headers
 )
 assert response.status_code == 204

 # Verify soft delete (product still in DB but is_active = False)
 await db_session.refresh(product)
 assert product.is_active is False


@pytest.mark.asyncio
async def test_get_product_not_found(client: AsyncClient, auth_headers: dict):
 """Test getting a non-existent product returns 404."""
 fake_uuid = "00000000-0000-0000-0000-000000000000"
 response = await client.get(f"/api/v1/products/{fake_uuid}", headers=auth_headers)
 assert response.status_code == 404
```

**Run tests**:
```bash
# All tests
uv run pytest backend/tests/integration/test_products.py -v

# Specific test
uv run pytest backend/tests/integration/test_products.py::test_create_product -v

# With coverage
uv run pytest backend/tests/integration/test_products.py --cov=app
```

---

## Common Feature Types

### 1. Simple CRUD (Products, Items)

**Characteristics**:
- Standard create, read, update, delete operations
- Single database (usually PostgreSQL)
- Straightforward relationships

**Steps**: Follow all 9 steps above

**Time**: 1-2 hours

### 2. Complex Business Logic (Order Processing)

**Characteristics**:
- Multi-step workflows
- Complex validation rules
- Multiple database operations in transaction

**Example**: Order placement
- Validate stock availability
- Calculate pricing (base price + discounts + taxes)
- Reserve inventory
- Create order record
- Send confirmation

**Key Difference**: Heavy service layer with business rules

**Time**: 2-4 hours

### 3. Multi-Database Feature (Activity Tracking)

**Characteristics**:
- Uses both PostgreSQL and MongoDB
- PostgreSQL for core data
- MongoDB for logs/events

**Example**: User activity tracking
- User model in PostgreSQL (structured)
- Activity logs in MongoDB (high write volume, flexible)

**Implementation**:
```python
# Service coordinates both databases
class ActivityService:
 def __init__(
 self,
 user_repo: UserRepository, # PostgreSQL
 event_repo: EventRepository # MongoDB
 ):
 self.user_repo = user_repo
 self.event_repo = event_repo

 async def track_login(self, user_id: UUID, ip_address: str):
 # Update last_login in PostgreSQL
 await self.user_repo.update_last_login(user_id)

 # Log event in MongoDB
 await self.event_repo.create_event({
 "event_type": "user_login",
 "user_id": str(user_id),
 "metadata": {"ip_address": ip_address}
 })
```

**Time**: 3-5 hours

### 4. Read-Only Feature (Dashboard Metrics)

**Characteristics**:
- No create/update/delete operations
- Aggregations and analytics
- Can use MongoDB for flexibility

**Steps**: Skip create/update/delete, focus on queries

**Time**: 1-2 hours

---

## Integration with Frontend

### Type Generation Flow

**After implementing backend**, generate TypeScript types for frontend:

```bash
# 1. Ensure backend is running
curl http://localhost:8000/docs

# 2. Generate types
cd frontend
npm run generate:types

# 3. Verify generated types
cat src/types/generated/api.ts | grep "ProductResponse"
```

**Output**: Frontend gets TypeScript interfaces matching backend Pydantic schemas:
```typescript
export interface ProductResponse {
 id: string;
 name: string;
 description?: string;
 sku: string;
 price: number;
 stock_quantity: number;
 category_id: string;
 is_active: boolean;
 created_at: string;
 updated_at: string;
}

export enum Permission {
 PRODUCTS_READ = "products:read",
 PRODUCTS_WRITE = "products:write",
 PRODUCTS_DELETE = "products:delete",
}
```

### API Contract

**REST Conventions** used in this boilerplate:

```
GET /api/v1/products # List (paginated)
POST /api/v1/products # Create (returns 201)
GET /api/v1/products/{id} # Get single
PATCH /api/v1/products/{id} # Partial update
DELETE /api/v1/products/{id} # Delete (returns 204)
```

**Response Format**:
```json
// Single resource
{
 "id": "uuid",
 "name": "Product Name",
 ...
}

// List
{
 "items": [...],
 "total": 100,
 "page": 1,
 "size": 10
}

// Error
{
 "detail": "Error message"
}
```

---

## Testing Strategy

### Unit Tests (Services & Repositories)

**Repository Tests** (`backend/tests/unit/repositories/`):
```python
@pytest.mark.asyncio
async def test_repository_get_by_id(db_session):
 """Test fetching product by ID."""
 repo = ProductRepository(db_session)

 # Create test product
 product = Product(name="Test", sku="TEST", price=9.99, ...)
 db_session.add(product)
 await db_session.commit()

 # Fetch by ID
 result = await repo.get_by_id(product.id)
 assert result is not None
 assert result.name == "Test"
```

**Service Tests** (`backend/tests/unit/services/`):
```python
@pytest.mark.asyncio
async def test_service_get_product_not_found():
 """Test service raises exception when product not found."""
 mock_repo = Mock(spec=ProductRepository)
 mock_repo.get_by_id.return_value = None

 service = ProductService(mock_repo)

 with pytest.raises(NotFoundException):
 await service.get_product("fake-uuid")
```

### Integration Tests (Full Endpoints)

**Test Complete Request/Response Cycle** (`backend/tests/integration/`):
- Authentication
- Permission checks
- Database operations
- Response format

**Fixtures**:
```python
@pytest.fixture
async def admin_user(db_session):
 """Create admin user with full permissions."""
 user = User(email="admin@test.com", ...)
 db_session.add(user)
 await db_session.commit()
 return user

@pytest.fixture
def admin_headers(admin_user):
 """Generate auth headers for admin."""
 token = create_access_token(admin_user.id)
 return {"Authorization": f"Bearer {token}"}
```

### Running Tests

```bash
# All tests
uv run pytest

# Unit tests only
uv run pytest backend/tests/unit/

# Integration tests only
uv run pytest backend/tests/integration/

# Specific file
uv run pytest backend/tests/integration/test_products.py

# With coverage report
uv run pytest --cov=app --cov-report=html

# Watch mode (re-run on changes)
uv run pytest-watch
```

---

## Tips & Best Practices

### Database

**DO**:
- [X] Choose PostgreSQL for relational data with ACID requirements
- [X] Choose MongoDB for flexible schemas and high write volume
- [X] Index foreign keys and frequently queried fields
- [X] Use soft delete (`is_active = False`) instead of hard delete
- [X] Always add `created_at` and `updated_at` timestamps

**DON'T**:
- [-] Store same logical data in both databases
- [-] Use MongoDB just because "NoSQL is faster" (choose based on data structure)
- [-] Skip migration review (always check before applying)
- [-] Use `float` for money (use `Decimal`)

### Code Quality

**DO**:
- [X] Add docstrings to all modules, classes, and functions
- [X] Use type hints (`Mapped[]`, function parameters)
- [X] Follow repository → service → API layering
- [X] Validate input in Pydantic schemas
- [X] Handle exceptions with custom exception classes

**DON'T**:
- [-] Put business logic in routes (belongs in service layer)
- [-] Put business logic in repositories (only data access)
- [-] Skip docstrings (Ruff will fail)

### Security

**DO**:
- [X] Hash passwords in services using `security.get_password_hash()`
- [X] Check permissions at API layer with `require_permissions()`
- [X] Validate all input via Pydantic schemas
- [X] Use UUIDs for IDs (not sequential integers)
- [X] Sanitize database queries (SQLAlchemy prevents SQL injection)

**DON'T**:
- [-] Hash passwords in models (do it in services)
- [-] Store passwords in plain text
- [-] Trust user input without validation
- [-] Return sensitive data in API responses (filter in schemas)

### Performance

**DO**:
- [X] Use `async`/`await` throughout
- [X] Batch database operations when possible
- [X] Add indexes to frequently queried columns
- [X] Use pagination for list endpoints (`skip`/`limit`)
- [X] Use `selectinload()` to avoid N+1 queries

**DON'T**:
- [-] Load all records without pagination
- [-] Make repeated database calls in loops (use joins or batch queries)
- [-] Over-index (indexes have write cost)

### Error Handling

**DO**:
- [X] Raise specific exceptions (`NotFoundException`, `ForbiddenException`)
- [X] Include helpful error messages
- [X] Return appropriate HTTP status codes (404, 403, 400, etc.)
- [X] Log errors for debugging

**DON'T**:
- [-] Return generic "Internal Server Error" messages
- [-] Expose sensitive details in error responses
- [-] Swallow exceptions without logging

---

## Common Issues

### Migration Conflicts

**Problem**: Migration fails with "table already exists"

**Solution**:
```bash
# Rollback one migration
uv run alembic downgrade -1

# Re-run migration
uv run alembic upgrade head

# Or skip migration if already applied manually
uv run alembic stamp head
```

### Circular Imports

**Problem**: `ImportError: cannot import name 'X' from partially initialized module`

**Solution**:
- Move imports inside functions
- Use `TYPE_CHECKING` for type hints only:
 ```python
 from typing import TYPE_CHECKING

 if TYPE_CHECKING:
 from app.models.category import Category
 ```

### Type Errors

**Problem**: mypy reports type errors

**Solution**:
```bash
# Run mypy to see all errors
uv run mypy app

# Common fixes:
# - Add type hints to function parameters
# - Use Optional[] for nullable fields
# - Use list[] instead of List (Python 3.9+)
```

### Permission Denied

**Problem**: User can't access endpoint even with correct credentials

**Solution**:
- Check user has required role assigned in database
- Verify role has required permission
- Check endpoint uses correct permission in `require_permissions()`
- Verify token contains permissions (decode JWT token)

---

## Next Steps

After implementing a feature:

1. **Run Tests**: `uv run pytest backend/tests/`
2. **Check Types**: `uv run mypy app`
3. **Format Code**: `uv run ruff format app tests`
4. **Lint Code**: `uv run ruff check --fix app tests`
5. **Test API**: Open http://localhost:8000/docs and test endpoints
6. **Generate Frontend Types**: `cd frontend && npm run generate:types`
7. **Commit**: Create atomic commit with clear message

---

## Additional Resources

- **Architecture Details**: See `docs/ARCHITECTURE.md` for system design
- **Frontend Integration**: See `frontend/docs/FEATURE_WORKFLOW.md` for frontend workflow
- **Fullstack Workflow**: See `docs/FULLSTACK_WORKFLOW.md` for complete E2E workflows
- **API Patterns**: See `docs/prompts/integration-patterns.md` for detailed API patterns

---

## Claude Code Integration (Optional)

This boilerplate includes Claude Code skills for faster development:

- `/fastapi-model` - Generate model with boilerplate
- `/fastapi-migration` - Create Alembic migration
- `/fastapi-permission` - Add permissions to RBAC
- `/fastapi-endpoint` - Generate complete CRUD endpoint
- `/fastapi-test` - Generate test files

**See**: `CLAUDE_CODE_BEST_PRACTICES.md` for Claude Code optimization strategies.

**Note**: These skills are optional tools. This workflow works with any IDE or editor.
