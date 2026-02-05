---
name: fastapi-endpoint
description: Create a complete CRUD endpoint with model, schema, repository, service, and router following project conventions
---

# FastAPI Endpoint Creation

Create a complete CRUD resource following the project's layered architecture.

## Prerequisites

- PostgreSQL database running
- Alembic migrations set up

## Required Information

Before starting, gather:
1. **Resource name** (singular, e.g., "product", "order", "comment")
2. **Fields** with types and constraints
3. **Relationships** (foreign keys to other tables)
4. **Ownership** - Does the resource belong to a user?
5. **Permissions required** (existing or new)

## Step-by-Step Creation

### Step 1: Create the SQLAlchemy Model

Create `app/models/postgres/{resource}.py`:

```python
"""
{Resource} model for PostgreSQL.
"""
from datetime import datetime, UTC
from uuid import UUID, uuid4

from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base


class {Resource}(Base):
 """
 {Resource} model.
 """

 __tablename__ = "{resources}" # plural, snake_case

 # Primary key - ALWAYS use UUID
 id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

 # Resource fields
 # title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
 # description: Mapped[str | None] = mapped_column(Text, nullable=True)

 # Foreign key (if owned by user)
 owner_id: Mapped[UUID] = mapped_column(
 ForeignKey("users.id", ondelete="CASCADE"),
 nullable=False,
 index=True,
 )

 # Status for soft delete: active, inactive
 status: Mapped[str] = mapped_column(
 String(20),
 nullable=False,
 default="active",
 index=True,
 )

 # Timestamps - ALWAYS include these
 created_at: Mapped[datetime] = mapped_column(
 DateTime(timezone=True),
 nullable=False,
 default=lambda: datetime.now(UTC),
 )
 updated_at: Mapped[datetime] = mapped_column(
 DateTime(timezone=True),
 nullable=False,
 default=lambda: datetime.now(UTC),
 onupdate=lambda: datetime.now(UTC),
 )

 def __repr__(self) -> str:
 return f"<{Resource} {self.id}>"

 @property
 def is_active(self) -> bool:
 """Check if resource is active."""
 return self.status == "active"
```

**Field Type Reference:**
- `String(255)` - short text
- `Text` - long text
- `Integer` - whole numbers
- `Float` - decimals
- `Boolean` - true/false
- `DateTime(timezone=True)` - timestamps
- `ARRAY(String(100))` - list of strings (PostgreSQL)
- `UUID` - foreign keys

### Step 2: Create Pydantic Schemas

Create `app/schemas/{resource}.py`:

```python
"""
Pydantic schemas for {Resource} API endpoints.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# Base schema with common fields
class {Resource}Base(BaseModel):
 """Base {resource} schema with common fields."""

 title: str = Field(min_length=1, max_length=255)
 description: str | None = None


# Create request schema
class {Resource}Create({Resource}Base):
 """Schema for creating a new {resource}."""

 pass # Inherits all fields from Base


# Update request schema - ALL FIELDS OPTIONAL
class {Resource}Update(BaseModel):
 """Schema for updating a {resource}."""

 title: str | None = Field(None, min_length=1, max_length=255)
 description: str | None = None


# Response schema
class {Resource}Response({Resource}Base):
 """Schema for {resource} response."""

 model_config = ConfigDict(from_attributes=True)

 id: UUID
 owner_id: UUID
 status: str
 created_at: datetime
 updated_at: datetime


# List response schema with pagination
class {Resource}ListResponse(BaseModel):
 """Schema for paginated {resource} list."""

 {resources}: list[{Resource}Response] # plural
 total: int
 skip: int
 limit: int
```

Then add exports to `app/schemas/__init__.py`:

```python
from app.schemas.{resource} import (
 {Resource}Base,
 {Resource}Create,
 {Resource}Update,
 {Resource}Response,
 {Resource}ListResponse,
)
```

### Step 3: Create Repository

Create `app/repositories/{resource}_repo.py`:

```python
"""
{Resource} repository for data access operations.
"""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.postgres.{resource} import {Resource}
from app.repositories.base import BaseRepository
from app.common.logging import get_logger

logger = get_logger(__name__)


class {Resource}Repository(BaseRepository[{Resource}]):
 """Repository for {Resource} model."""

 def __init__(self, db: AsyncSession):
 super().__init__({Resource}, db)

 async def get_by_owner(
 self,
 owner_id: UUID,
 skip: int = 0,
 limit: int = 100,
 ) -> list[{Resource}]:
 """Get all {resources} owned by a specific user."""
 result = await self.db.execute(
 select({Resource})
 .where({Resource}.owner_id == owner_id)
 .where({Resource}.status == "active")
 .offset(skip)
 .limit(limit)
 )
 items = list(result.scalars().all())

 logger.debug(
 "{resource}_get_by_owner",
 owner_id=str(owner_id),
 count=len(items),
 )

 return items

 async def count_by_owner(self, owner_id: UUID) -> int:
 """Count {resources} owned by a specific user."""
 return await self.count(filters={"owner_id": owner_id, "status": "active"})
```

Add to `app/repositories/__init__.py`:

```python
from app.repositories.{resource}_repo import {Resource}Repository
```

### Step 4: Create Service

Create `app/services/{resource}_service.py`:

```python
"""
{Resource} service with business logic.
"""
from uuid import UUID

from app.repositories.{resource}_repo import {Resource}Repository
from app.models.postgres.{resource} import {Resource}
from app.models.postgres.user import User
from app.schemas.{resource} import {Resource}Create, {Resource}Update
from app.common.logging import get_logger
from app.common.exceptions import NotFoundError, ValidationError

logger = get_logger(__name__)


class {Resource}Service:
 """Service for {resource} business logic."""

 def __init__(self, {resource}_repo: {Resource}Repository):
 self.{resource}_repo = {resource}_repo

 async def get_{resource}(self, {resource}_id: UUID, current_user: User) -> {Resource}:
 """Get {resource} by ID."""
 {resource} = await self.{resource}_repo.get({resource}_id)
 if not {resource} or {resource}.status != "active":
 raise NotFoundError(
 message="{Resource} not found",
 details={"{resource}_id": str({resource}_id)},
 )

 # Check ownership (admin can see any)
 if {resource}.owner_id != current_user.id and not current_user.is_admin:
 raise ValidationError(
 message="You don't have access to this {resource}",
 details={"{resource}_id": str({resource}_id)},
 )

 return {resource}

 async def list_{resources}(
 self,
 current_user: User,
 skip: int = 0,
 limit: int = 100,
 ) -> tuple[list[{Resource}], int]:
 """List {resources} for current user."""
 if current_user.is_admin:
 items = await self.{resource}_repo.get_all(
 skip=skip,
 limit=limit,
 filters={"status": "active"},
 )
 total = await self.{resource}_repo.count(filters={"status": "active"})
 else:
 items = await self.{resource}_repo.get_by_owner(
 owner_id=current_user.id,
 skip=skip,
 limit=limit,
 )
 total = await self.{resource}_repo.count_by_owner(current_user.id)

 return items, total

 async def create_{resource}(self, data: {Resource}Create, owner: User) -> {Resource}:
 """Create a new {resource}."""
 {resource} = {Resource}(
 # Map fields from schema to model
 title=data.title,
 description=data.description,
 owner_id=owner.id,
 status="active",
 )

 created = await self.{resource}_repo.create({resource})

 logger.info(
 "{resource}_created",
 {resource}_id=str(created.id),
 owner_id=str(owner.id),
 )

 return created

 async def update_{resource}(
 self,
 {resource}_id: UUID,
 data: {Resource}Update,
 current_user: User,
 ) -> {Resource}:
 """Update a {resource}."""
 # Get and verify ownership
 {resource} = await self.get_{resource}({resource}_id, current_user)

 if {resource}.owner_id != current_user.id and not current_user.is_admin:
 raise ValidationError(
 message="You don't have permission to update this {resource}",
 details={"{resource}_id": str({resource}_id)},
 )

 update_dict = data.model_dump(exclude_unset=True)
 updated = await self.{resource}_repo.update({resource}_id, update_dict)

 if not updated:
 raise NotFoundError(
 message="{Resource} not found",
 details={"{resource}_id": str({resource}_id)},
 )

 logger.info(
 "{resource}_updated",
 {resource}_id=str({resource}_id),
 updated_by=str(current_user.id),
 )

 return updated

 async def delete_{resource}(self, {resource}_id: UUID, current_user: User) -> None:
 """Delete a {resource} (soft delete)."""
 {resource} = await self.get_{resource}({resource}_id, current_user)

 if {resource}.owner_id != current_user.id and not current_user.is_admin:
 raise ValidationError(
 message="You don't have permission to delete this {resource}",
 details={"{resource}_id": str({resource}_id)},
 )

 await self.{resource}_repo.soft_delete({resource}_id)

 logger.info(
 "{resource}_deleted",
 {resource}_id=str({resource}_id),
 deleted_by=str(current_user.id),
 )
```

Add to `app/services/__init__.py`:

```python
from app.services.{resource}_service import {Resource}Service
```

### Step 5: Add Dependencies

Add to `app/api/deps.py`:

```python
from app.repositories.{resource}_repo import {Resource}Repository
from app.services.{resource}_service import {Resource}Service

# Repository dependency
async def get_{resource}_repository(
 db: Annotated[AsyncSession, Depends(get_db)]
) -> {Resource}Repository:
 """Get {resource} repository instance."""
 return {Resource}Repository(db)

# Service dependency
async def get_{resource}_service(
 {resource}_repo: Annotated[{Resource}Repository, Depends(get_{resource}_repository)]
) -> {Resource}Service:
 """Get {resource} service instance."""
 return {Resource}Service({resource}_repo)

# Type alias
{Resource}Svc = Annotated[{Resource}Service, Depends(get_{resource}_service)]
{Resource}Repo = Annotated[{Resource}Repository, Depends(get_{resource}_repository)]
```

### Step 6: Create Router

Create `app/api/v1/{resources}.py` (plural filename):

```python
"""
{Resource} API endpoints.
"""
from uuid import UUID

from fastapi import APIRouter, status, HTTPException

from app.api.deps import CurrentUser, {Resource}Svc
from app.schemas.{resource} import (
 {Resource}Create,
 {Resource}Update,
 {Resource}Response,
 {Resource}ListResponse,
)
from app.common.logging import get_logger
from app.common.exceptions import NotFoundError, ValidationError

logger = get_logger(__name__)

router = APIRouter(prefix="/{resources}", tags=["{resources}"])


@router.post(
 "/",
 response_model={Resource}Response,
 status_code=status.HTTP_201_CREATED,
 summary="Create {resource}",
 description="Create a new {resource}.",
)
async def create_{resource}(
 data: {Resource}Create,
 current_user: CurrentUser,
 {resource}_service: {Resource}Svc,
) -> {Resource}Response:
 """Create a new {resource}."""
 {resource} = await {resource}_service.create_{resource}(data, current_user)
 return {Resource}Response.model_validate({resource})


@router.get(
 "/",
 response_model={Resource}ListResponse,
 summary="List {resources}",
 description="List {resources}. Users see their own, admins see all.",
)
async def list_{resources}(
 current_user: CurrentUser,
 {resource}_service: {Resource}Svc,
 skip: int = 0,
 limit: int = 100,
) -> {Resource}ListResponse:
 """List {resources} with pagination."""
 items, total = await {resource}_service.list_{resources}(current_user, skip, limit)

 return {Resource}ListResponse(
 {resources}=[{Resource}Response.model_validate(i) for i in items],
 total=total,
 skip=skip,
 limit=limit,
 )


@router.get(
 "/{{resource}_id}",
 response_model={Resource}Response,
 summary="Get {resource}",
 description="Get a specific {resource} by ID.",
)
async def get_{resource}(
 {resource}_id: UUID,
 current_user: CurrentUser,
 {resource}_service: {Resource}Svc,
) -> {Resource}Response:
 """Get {resource} by ID."""
 try:
 {resource} = await {resource}_service.get_{resource}({resource}_id, current_user)
 return {Resource}Response.model_validate({resource})
 except NotFoundError as e:
 raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
 except ValidationError as e:
 raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)


@router.patch(
 "/{{resource}_id}",
 response_model={Resource}Response,
 summary="Update {resource}",
 description="Update a {resource}. Only owner or admin can update.",
)
async def update_{resource}(
 {resource}_id: UUID,
 data: {Resource}Update,
 current_user: CurrentUser,
 {resource}_service: {Resource}Svc,
) -> {Resource}Response:
 """Update {resource}."""
 try:
 {resource} = await {resource}_service.update_{resource}({resource}_id, data, current_user)
 return {Resource}Response.model_validate({resource})
 except NotFoundError as e:
 raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
 except ValidationError as e:
 raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)


@router.delete(
 "/{{resource}_id}",
 status_code=status.HTTP_204_NO_CONTENT,
 summary="Delete {resource}",
 description="Delete a {resource} (soft delete). Only owner or admin.",
)
async def delete_{resource}(
 {resource}_id: UUID,
 current_user: CurrentUser,
 {resource}_service: {Resource}Svc,
) -> None:
 """Delete {resource}."""
 try:
 await {resource}_service.delete_{resource}({resource}_id, current_user)
 except NotFoundError as e:
 raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
 except ValidationError as e:
 raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)
```

### Step 7: Register Router

Add to `app/api/v1/router.py`:

```python
from app.api.v1 import {resources}

api_router.include_router({resources}.router)
```

### Step 8: Create Migration

1. Import model in `alembic/env.py`:
 ```python
 from app.models.postgres import {resource} # noqa: F401
 ```

2. Generate migration:
 ```bash
 uv run alembic revision --autogenerate -m "add {resources} table"
 ```

3. Review the generated migration file in `alembic/versions/`

4. Apply migration:
 ```bash
 uv run alembic upgrade head
 ```

### Step 9: Test the Endpoint

```bash
# Start server
uv run dev

# Test via Swagger UI
open http://localhost:8000/docs
```

## Checklist

- [ ] Model created in `app/models/postgres/{resource}.py`
- [ ] Model imported in `alembic/env.py`
- [ ] Schemas created in `app/schemas/{resource}.py`
- [ ] Schemas exported in `app/schemas/__init__.py`
- [ ] Repository created in `app/repositories/{resource}_repo.py`
- [ ] Repository exported in `app/repositories/__init__.py`
- [ ] Service created in `app/services/{resource}_service.py`
- [ ] Service exported in `app/services/__init__.py`
- [ ] Dependencies added to `app/api/deps.py`
- [ ] Router created in `app/api/v1/{resources}.py`
- [ ] Router registered in `app/api/v1/router.py`
- [ ] Migration generated and applied
- [ ] Endpoint tested
