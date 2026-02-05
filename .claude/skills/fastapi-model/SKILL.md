---
name: fastapi-model
description: Create SQLAlchemy models for PostgreSQL with proper typing, relationships, and conventions
---

# PostgreSQL Model Creation

Create SQLAlchemy models following project patterns and conventions.

## Model Location

All PostgreSQL models go in: `app/models/postgres/{model_name}.py`

## Basic Model Template

```python
"""
{Model} model for PostgreSQL.
"""
from datetime import datetime, UTC
from uuid import UUID, uuid4

from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.postgres import Base


class {Model}(Base):
 """
 {Model} model description.
 """

 __tablename__ = "{models}" # plural, snake_case

 # ==========================================================================
 # Primary Key - ALWAYS UUID
 # ==========================================================================
 id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

 # ==========================================================================
 # Fields
 # ==========================================================================
 name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
 description: Mapped[str | None] = mapped_column(Text, nullable=True)

 # ==========================================================================
 # Foreign Keys (if any)
 # ==========================================================================
 owner_id: Mapped[UUID] = mapped_column(
 ForeignKey("users.id", ondelete="CASCADE"),
 nullable=False,
 index=True,
 )

 # ==========================================================================
 # Status - for soft delete
 # ==========================================================================
 status: Mapped[str] = mapped_column(
 String(20),
 nullable=False,
 default="active",
 index=True,
 )

 # ==========================================================================
 # Timestamps - ALWAYS include
 # ==========================================================================
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

 # ==========================================================================
 # Methods
 # ==========================================================================
 def __repr__(self) -> str:
 return f"<{Model} {self.name}>"

 @property
 def is_active(self) -> bool:
 """Check if model is active."""
 return self.status == "active"
```

## Field Types Reference

### Basic Types

| Python Type | SQLAlchemy Type | Usage |
|-------------|-----------------|-------|
| `str` | `String(n)` | Short text (max n chars) |
| `str` | `Text` | Long text (unlimited) |
| `int` | `Integer` | Whole numbers |
| `float` | `Float` | Decimal numbers |
| `bool` | `Boolean` | True/False |
| `datetime` | `DateTime(timezone=True)` | Timestamps |
| `UUID` | (auto-detected) | IDs and foreign keys |

### PostgreSQL-Specific Types

```python
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PG_UUID

# Array of strings
tags: Mapped[list[str] | None] = mapped_column(
 ARRAY(String(100)),
 nullable=True,
 default=None,
)

# JSON data
metadata: Mapped[dict | None] = mapped_column(
 JSONB,
 nullable=True,
 default=None,
)
```

### Nullable vs Non-Nullable

```python
# Required field (NOT NULL)
name: Mapped[str] = mapped_column(String(255), nullable=False)

# Optional field (NULL allowed)
description: Mapped[str | None] = mapped_column(Text, nullable=True)
```

### Defaults

```python
# Static default
status: Mapped[str] = mapped_column(String(20), default="active")

# Dynamic default (function)
created_at: Mapped[datetime] = mapped_column(
 DateTime(timezone=True),
 default=lambda: datetime.now(UTC),
)

# Auto-update on modification
updated_at: Mapped[datetime] = mapped_column(
 DateTime(timezone=True),
 default=lambda: datetime.now(UTC),
 onupdate=lambda: datetime.now(UTC),
)
```

### Indexes

```python
# Simple index (for filtering/sorting)
email: Mapped[str] = mapped_column(String(255), index=True)

# Unique index (prevents duplicates)
email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
```

## Foreign Keys & Relationships

### One-to-Many (Parent has many Children)

```python
# In Category model (parent)
class Category(Base):
 __tablename__ = "categories"

 id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
 name: Mapped[str] = mapped_column(String(100), nullable=False)

 # Relationship to children
 products: Mapped[list["Product"]] = relationship(
 "Product",
 back_populates="category",
 lazy="selectin",
 )


# In Product model (child)
class Product(Base):
 __tablename__ = "products"

 id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
 name: Mapped[str] = mapped_column(String(255), nullable=False)

 # Foreign key
 category_id: Mapped[UUID] = mapped_column(
 ForeignKey("categories.id", ondelete="SET NULL"),
 nullable=True,
 index=True,
 )

 # Relationship to parent
 category: Mapped["Category | None"] = relationship(
 "Category",
 back_populates="products",
 )
```

### Many-to-Many

```python
# Association table
product_tags = Table(
 "product_tags",
 Base.metadata,
 Column("product_id", ForeignKey("products.id", ondelete="CASCADE"), primary_key=True),
 Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Product(Base):
 __tablename__ = "products"

 id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
 name: Mapped[str] = mapped_column(String(255), nullable=False)

 # Many-to-many relationship
 tags: Mapped[list["Tag"]] = relationship(
 "Tag",
 secondary=product_tags,
 back_populates="products",
 lazy="selectin",
 )


class Tag(Base):
 __tablename__ = "tags"

 id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
 name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

 # Many-to-many relationship
 products: Mapped[list["Product"]] = relationship(
 "Product",
 secondary=product_tags,
 back_populates="tags",
 lazy="selectin",
 )
```

### Self-Referential (Tree Structure)

```python
class Category(Base):
 __tablename__ = "categories"

 id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
 name: Mapped[str] = mapped_column(String(100), nullable=False)

 # Parent reference
 parent_id: Mapped[UUID | None] = mapped_column(
 ForeignKey("categories.id", ondelete="CASCADE"),
 nullable=True,
 index=True,
 )

 # Relationships
 parent: Mapped["Category | None"] = relationship(
 "Category",
 remote_side=[id],
 back_populates="children",
 )
 children: Mapped[list["Category"]] = relationship(
 "Category",
 back_populates="parent",
 lazy="selectin",
 )
```

## ondelete Options

| Option | Behavior |
|--------|----------|
| `CASCADE` | Delete children when parent deleted |
| `SET NULL` | Set FK to NULL when parent deleted |
| `RESTRICT` | Prevent deletion if children exist |
| `SET DEFAULT` | Set FK to default value |

## Complete Examples

### User Model (with RBAC)

```python
"""User model with role-based permissions."""
from datetime import datetime, UTC
from uuid import UUID, uuid4

from sqlalchemy import String, DateTime
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base


class User(Base):
 __tablename__ = "users"

 id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

 # Authentication
 email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
 password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

 # Profile
 first_name: Mapped[str] = mapped_column(String(100), nullable=False)
 last_name: Mapped[str] = mapped_column(String(100), nullable=False)

 # RBAC
 role: Mapped[str] = mapped_column(String(50), nullable=False, default="user", index=True)
 custom_permissions: Mapped[list[str] | None] = mapped_column(
 ARRAY(String(100)), nullable=True, default=None
 )

 # Status
 status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", index=True)

 # Timestamps
 created_at: Mapped[datetime] = mapped_column(
 DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
 )
 updated_at: Mapped[datetime] = mapped_column(
 DateTime(timezone=True), nullable=False,
 default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
 )

 def __repr__(self) -> str:
 return f"<User {self.email}>"

 @property
 def full_name(self) -> str:
 return f"{self.first_name} {self.last_name}"

 @property
 def is_active(self) -> bool:
 return self.status == "active"

 @property
 def is_admin(self) -> bool:
 return self.role == "admin"
```

### Order Model (with relationships)

```python
"""Order model with line items."""
from datetime import datetime, UTC
from uuid import UUID, uuid4
from decimal import Decimal

from sqlalchemy import String, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.postgres import Base


class Order(Base):
 __tablename__ = "orders"

 id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

 # Customer
 customer_id: Mapped[UUID] = mapped_column(
 ForeignKey("users.id", ondelete="CASCADE"),
 nullable=False,
 index=True,
 )
 customer: Mapped["User"] = relationship("User", lazy="selectin")

 # Order details
 order_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
 total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

 # Status: pending, confirmed, shipped, delivered, cancelled
 status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)

 # Line items
 items: Mapped[list["OrderItem"]] = relationship(
 "OrderItem",
 back_populates="order",
 lazy="selectin",
 cascade="all, delete-orphan",
 )

 # Timestamps
 created_at: Mapped[datetime] = mapped_column(
 DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
 )
 updated_at: Mapped[datetime] = mapped_column(
 DateTime(timezone=True), nullable=False,
 default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
 )


class OrderItem(Base):
 __tablename__ = "order_items"

 id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

 # Parent order
 order_id: Mapped[UUID] = mapped_column(
 ForeignKey("orders.id", ondelete="CASCADE"),
 nullable=False,
 index=True,
 )
 order: Mapped["Order"] = relationship("Order", back_populates="items")

 # Product reference
 product_id: Mapped[UUID] = mapped_column(
 ForeignKey("products.id", ondelete="RESTRICT"),
 nullable=False,
 )

 # Snapshot of product at time of order
 product_name: Mapped[str] = mapped_column(String(255), nullable=False)
 unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
 quantity: Mapped[int] = mapped_column(nullable=False)

 @property
 def line_total(self) -> Decimal:
 return self.unit_price * self.quantity
```

## After Creating a Model

1. **Import in alembic/env.py**:
 ```python
 from app.models.postgres import your_model # noqa: F401
 ```

2. **Generate migration**:
 ```bash
 uv run alembic revision --autogenerate -m "add your_model table"
 ```

3. **Review and apply**:
 ```bash
 uv run alembic upgrade head
 ```

## Checklist

- [ ] Model file created in `app/models/postgres/`
- [ ] Inherits from `Base`
- [ ] UUID primary key with `default=uuid4`
- [ ] Proper `__tablename__` (plural, snake_case)
- [ ] All fields have type hints (`Mapped[T]`)
- [ ] Nullable fields use `Mapped[T | None]`
- [ ] `status` field for soft delete (if needed)
- [ ] `created_at` and `updated_at` timestamps
- [ ] Foreign keys with appropriate `ondelete`
- [ ] Indexes on frequently queried fields
- [ ] `__repr__` method defined
- [ ] Model imported in `alembic/env.py`
- [ ] Migration generated and applied
