---
name: fastapi-migration
description: Create, manage, and troubleshoot Alembic database migrations for PostgreSQL
---

# Alembic Migration Workflow

Manage PostgreSQL schema changes using Alembic migrations.

## Quick Reference

```bash
# Apply all pending migrations
uv run alembic upgrade head

# Create new migration (autogenerate from models)
uv run alembic revision --autogenerate -m "description"

# Revert last migration
uv run alembic downgrade -1

# Show current revision
uv run alembic current

# Show migration history
uv run alembic history

# Reset database (revert all + apply all)
uv run alembic downgrade base && uv run alembic upgrade head
```

## Creating a New Migration

### Step 1: Modify the Model

Edit or create your model in `app/models/postgres/{resource}.py`.

**Example - Adding a field:**

```python
# Before
class User(Base):
 __tablename__ = "users"
 id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
 email: Mapped[str] = mapped_column(String(255), unique=True)

# After - adding phone_number field
class User(Base):
 __tablename__ = "users"
 id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
 email: Mapped[str] = mapped_column(String(255), unique=True)
 phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True) # NEW
```

### Step 2: Register Model (for new models only)

If creating a new model, import it in `alembic/env.py`:

```python
# alembic/env.py
from app.models.postgres import user, item # noqa: F401
from app.models.postgres import your_new_model # noqa: F401 # ADD THIS
```

**CRITICAL**: Alembic can only detect models that are imported in env.py!

### Step 3: Generate Migration

```bash
uv run alembic revision --autogenerate -m "add phone_number to users"
```

This creates a file in `alembic/versions/` like:
`2024_01_15_1430-abc123_add_phone_number_to_users.py`

### Step 4: Review the Migration

**ALWAYS review generated migrations!** Alembic autogenerate is not perfect.

```python
# alembic/versions/2024_01_15_1430-abc123_add_phone_number_to_users.py

def upgrade() -> None:
 # Review these operations
 op.add_column('users', sa.Column('phone_number', sa.String(20), nullable=True))


def downgrade() -> None:
 # Review these operations
 op.drop_column('users', 'phone_number')
```

**Check for:**
- Correct table and column names
- Proper data types
- Nullable settings
- Index/constraint creation
- Safe downgrade path

### Step 5: Apply Migration

```bash
uv run alembic upgrade head
```

## Common Migration Scenarios

### Adding a Column

```python
def upgrade() -> None:
 op.add_column('users', sa.Column('phone_number', sa.String(20), nullable=True))

def downgrade() -> None:
 op.drop_column('users', 'phone_number')
```

### Adding a Non-Nullable Column (with default)

```python
def upgrade() -> None:
 # Step 1: Add column as nullable
 op.add_column('users', sa.Column('status', sa.String(20), nullable=True))

 # Step 2: Set default value for existing rows
 op.execute("UPDATE users SET status = 'active' WHERE status IS NULL")

 # Step 3: Make column non-nullable
 op.alter_column('users', 'status', nullable=False)

def downgrade() -> None:
 op.drop_column('users', 'status')
```

### Adding an Index

```python
def upgrade() -> None:
 op.create_index('ix_users_email', 'users', ['email'], unique=True)

def downgrade() -> None:
 op.drop_index('ix_users_email', 'users')
```

### Adding a Foreign Key

```python
def upgrade() -> None:
 op.add_column('items', sa.Column('category_id', postgresql.UUID(), nullable=True))
 op.create_foreign_key(
 'fk_items_category_id',
 'items', 'categories',
 ['category_id'], ['id'],
 ondelete='SET NULL'
 )

def downgrade() -> None:
 op.drop_constraint('fk_items_category_id', 'items', type_='foreignkey')
 op.drop_column('items', 'category_id')
```

### Creating a New Table

```python
def upgrade() -> None:
 op.create_table(
 'categories',
 sa.Column('id', postgresql.UUID(), primary_key=True),
 sa.Column('name', sa.String(100), nullable=False),
 sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
 )
 op.create_index('ix_categories_name', 'categories', ['name'])

def downgrade() -> None:
 op.drop_index('ix_categories_name', 'categories')
 op.drop_table('categories')
```

### Renaming a Column

```python
def upgrade() -> None:
 op.alter_column('users', 'name', new_column_name='full_name')

def downgrade() -> None:
 op.alter_column('users', 'full_name', new_column_name='name')
```

### Changing Column Type

```python
def upgrade() -> None:
 # Change from String(100) to String(255)
 op.alter_column(
 'users', 'email',
 type_=sa.String(255),
 existing_type=sa.String(100),
 )

def downgrade() -> None:
 op.alter_column(
 'users', 'email',
 type_=sa.String(100),
 existing_type=sa.String(255),
 )
```

## Troubleshooting

### "Target database is not up to date"

```bash
# Check current state
uv run alembic current

# Apply pending migrations
uv run alembic upgrade head
```

### "Can't locate revision"

Your database has a revision that doesn't exist in your codebase:

```bash
# See what revision the DB thinks it's at
uv run alembic current

# Option 1: Reset to base (LOSES DATA)
uv run alembic downgrade base
uv run alembic upgrade head

# Option 2: Stamp to specific revision
uv run alembic stamp head
```

### Autogenerate Doesn't Detect Changes

1. **Model not imported in env.py** - Most common cause
 ```python
 # alembic/env.py
 from app.models.postgres import your_model # noqa: F401
 ```

2. **Model doesn't inherit from Base**
 ```python
 from app.db.postgres import Base

 class YourModel(Base): # Must inherit from Base
 ...
 ```

3. **Table already exists** - Alembic thinks it's already created

### Migration Failed Halfway

If a migration fails partway through:

```bash
# Check current state
uv run alembic current

# Option 1: Fix the migration and retry
uv run alembic upgrade head

# Option 2: Manually revert changes in DB, then
uv run alembic stamp <previous_revision>
```

### Need to Modify an Applied Migration

**Never modify a migration that's been applied to any environment!**

Instead:
1. Create a new migration to make the fix
2. Or, if only local dev: `alembic downgrade -1`, delete migration, recreate

## Data Migrations

Sometimes you need to migrate data, not just schema:

```python
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session

def upgrade() -> None:
 # Get connection
 bind = op.get_bind()
 session = Session(bind=bind)

 # Perform data migration
 session.execute(sa.text("""
 UPDATE users
 SET role = 'admin'
 WHERE email IN ('admin@example.com')
 """))
 session.commit()

def downgrade() -> None:
 bind = op.get_bind()
 session = Session(bind=bind)

 session.execute(sa.text("""
 UPDATE users
 SET role = 'user'
 WHERE email IN ('admin@example.com')
 """))
 session.commit()
```

## Best Practices

1. **Always review autogenerated migrations** before applying
2. **Test migrations on a copy of production data** when possible
3. **Keep migrations small and focused** - one logical change per migration
4. **Write reversible migrations** - always implement downgrade
5. **Never edit applied migrations** - create new ones instead
6. **Name migrations descriptively** - `add_phone_to_users` not `update_table`

## Checklist for New Migrations

- [ ] Model changes made in `app/models/postgres/`
- [ ] Model imported in `alembic/env.py` (new models only)
- [ ] Migration generated: `uv run alembic revision --autogenerate -m "..."`
- [ ] Migration file reviewed for correctness
- [ ] Both upgrade() and downgrade() are correct
- [ ] Migration applied: `uv run alembic upgrade head`
- [ ] Database verified with queries or Swagger UI
