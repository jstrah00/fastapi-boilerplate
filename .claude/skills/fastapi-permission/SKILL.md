---
name: fastapi-permission
description: Add new permissions, roles, and role-based access control (RBAC) to endpoints
---

# Permission & RBAC Management

Add and manage role-based access control following project patterns.

## Permission System Overview

The project uses a flexible RBAC system defined in `app/common/permissions.py`:

```
Permission Enum → ROLE_PERMISSIONS mapping → require_permissions() dependency
```

**Authorization approaches:**
1. **Simple admin check**: `CurrentAdmin` dependency
2. **Fine-grained RBAC**: `require_permissions(Permission.X)` dependency

## Adding a New Permission

### Step 1: Define the Permission

Edit `app/common/permissions.py`:

```python
class Permission(str, Enum):
    """Permission definitions for the application."""

    # Existing permissions
    USERS_READ = "users:read"
    USERS_CREATE = "users:create"
    # ...

    # ADD YOUR NEW PERMISSIONS HERE
    # Format: RESOURCE_ACTION = "resource:action"
    REPORTS_VIEW = "reports:view"
    REPORTS_GENERATE = "reports:generate"
    REPORTS_EXPORT = "reports:export"

    ORDERS_READ = "orders:read"
    ORDERS_CREATE = "orders:create"
    ORDERS_UPDATE = "orders:update"
    ORDERS_CANCEL = "orders:cancel"
```

**Naming convention:** `RESOURCE_ACTION = "resource:action"`

### Step 2: Assign to Roles

Update `ROLE_PERMISSIONS` in the same file:

```python
ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.ADMIN: {
        # Admin gets everything
        Permission.USERS_READ,
        Permission.USERS_CREATE,
        # ... existing ...

        # NEW permissions for admin
        Permission.REPORTS_VIEW,
        Permission.REPORTS_GENERATE,
        Permission.REPORTS_EXPORT,
        Permission.ORDERS_READ,
        Permission.ORDERS_CREATE,
        Permission.ORDERS_UPDATE,
        Permission.ORDERS_CANCEL,
    },

    Role.USER: {
        # Regular user permissions
        Permission.ITEMS_READ,
        Permission.ITEMS_CREATE,
        # ... existing ...

        # NEW permissions for user (limited)
        Permission.REPORTS_VIEW,  # Can view but not generate
        Permission.ORDERS_READ,
        Permission.ORDERS_CREATE,
    },

    # Add to custom roles if you have them
}
```

### Step 3: Use in Endpoints

**Option A: Require specific permission(s)**

```python
from fastapi import Depends
from app.common.permissions import Permission, require_permissions
from app.models.postgres.user import User

@router.get("/reports")
async def view_reports(
    current_user: User = Depends(require_permissions(Permission.REPORTS_VIEW)),
):
    """View reports - requires REPORTS_VIEW permission."""
    ...

@router.post("/reports/generate")
async def generate_report(
    current_user: User = Depends(require_permissions(
        Permission.REPORTS_VIEW,
        Permission.REPORTS_GENERATE,  # Multiple permissions required
    )),
):
    """Generate reports - requires BOTH permissions."""
    ...
```

**Option B: Require ANY of several permissions**

```python
from app.common.permissions import require_any_permission

@router.get("/admin/dashboard")
async def admin_dashboard(
    current_user: User = Depends(require_any_permission(
        Permission.ADMIN_ACCESS,
        Permission.REPORTS_VIEW,
    )),
):
    """Dashboard - requires EITHER permission."""
    ...
```

**Option C: Simple admin check**

```python
from app.api.deps import CurrentAdmin

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: UUID,
    current_user: CurrentAdmin,  # Only admins
):
    """Delete user - admin only."""
    ...
```

## Adding a New Role

### Step 1: Define the Role

```python
class Role(str, Enum):
    """Role definitions."""

    ADMIN = "admin"
    USER = "user"
    # ADD NEW ROLE
    MANAGER = "manager"
    MODERATOR = "moderator"
    VIEWER = "viewer"
```

### Step 2: Assign Permissions

```python
ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.ADMIN: {...},
    Role.USER: {...},

    # NEW: Manager role
    Role.MANAGER: {
        Permission.USERS_READ,      # Can read users
        Permission.ITEMS_READ,
        Permission.ITEMS_CREATE,
        Permission.ITEMS_UPDATE,
        Permission.ITEMS_DELETE,    # Can delete items (unlike USER)
        Permission.REPORTS_VIEW,
        Permission.REPORTS_GENERATE,
    },

    # NEW: Moderator role
    Role.MODERATOR: {
        Permission.ITEMS_READ,
        Permission.ITEMS_UPDATE,    # Can edit items
        Permission.ITEMS_DELETE,    # Can delete items
    },

    # NEW: Viewer role (read-only)
    Role.VIEWER: {
        Permission.ITEMS_READ,
        Permission.REPORTS_VIEW,
    },
}
```

### Step 3: Update Schema Validation

Update `app/schemas/user.py` to allow the new role:

```python
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=100)

    # Update regex to include new roles
    role: str = Field(
        default="user",
        pattern="^(admin|user|manager|moderator|viewer)$"
    )
```

And `UserRoleUpdate`:

```python
class UserRoleUpdate(BaseModel):
    role: str | None = Field(
        None,
        pattern="^(admin|user|manager|moderator|viewer)$"
    )
```

## Custom Permissions per User

Users can have additional permissions beyond their role via `custom_permissions`:

### Granting Custom Permissions

```python
# In service or via API
user = await user_service.update_user_role(
    user_id=user_id,
    role_data=UserRoleUpdate(
        custom_permissions=["items:delete", "reports:generate"]
    ),
    current_user=admin,
)
```

### How It Works

The `get_user_permissions()` function combines role + custom permissions:

```python
def get_user_permissions(role: str, custom_permissions: list[str] | None = None) -> set[Permission]:
    """Get all permissions for a user."""
    permissions: set[Permission] = set()

    # Get from role
    role_enum = Role(role)
    permissions = ROLE_PERMISSIONS.get(role_enum, set()).copy()

    # Add custom permissions
    if custom_permissions:
        for perm_str in custom_permissions:
            perm = Permission(perm_str)
            permissions.add(perm)

    return permissions
```

## Checking Permissions in Service Layer

Sometimes you need to check permissions in business logic:

```python
from app.common.permissions import Permission, has_permission, has_any_permission

class OrderService:
    async def cancel_order(self, order_id: UUID, current_user: User) -> Order:
        # Check if user can cancel
        can_cancel = (
            order.owner_id == current_user.id  # Owner can cancel their own
            or has_permission(
                current_user.role,
                Permission.ORDERS_CANCEL,
                current_user.custom_permissions,
            )
        )

        if not can_cancel:
            raise ValidationError("You cannot cancel this order")

        # ... cancel logic
```

## Complete Example: Adding Reports Feature

### 1. Add Permissions

```python
# app/common/permissions.py

class Permission(str, Enum):
    # ... existing ...

    # Reports
    REPORTS_VIEW = "reports:view"
    REPORTS_GENERATE = "reports:generate"
    REPORTS_EXPORT = "reports:export"


ROLE_PERMISSIONS = {
    Role.ADMIN: {
        # ... existing ...
        Permission.REPORTS_VIEW,
        Permission.REPORTS_GENERATE,
        Permission.REPORTS_EXPORT,
    },
    Role.USER: {
        # ... existing ...
        Permission.REPORTS_VIEW,  # Users can only view
    },
}
```

### 2. Create Router with Permission Checks

```python
# app/api/v1/reports.py

from fastapi import APIRouter, Depends
from app.common.permissions import Permission, require_permissions
from app.models.postgres.user import User

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/")
async def list_reports(
    current_user: User = Depends(require_permissions(Permission.REPORTS_VIEW)),
):
    """List available reports."""
    ...


@router.post("/generate")
async def generate_report(
    current_user: User = Depends(require_permissions(
        Permission.REPORTS_VIEW,
        Permission.REPORTS_GENERATE,
    )),
):
    """Generate a new report."""
    ...


@router.get("/{report_id}/export")
async def export_report(
    report_id: UUID,
    current_user: User = Depends(require_permissions(
        Permission.REPORTS_VIEW,
        Permission.REPORTS_EXPORT,
    )),
):
    """Export report to file."""
    ...
```

### 3. Register Router

```python
# app/api/v1/router.py
from app.api.v1 import reports

api_router.include_router(reports.router)
```

## Testing Permissions

```python
# tests/integration/test_reports.py

class TestReportPermissions:
    async def test_user_can_view_reports(
        self,
        client: AsyncClient,
        auth_headers: dict,  # Regular user
    ):
        """User with REPORTS_VIEW should access list."""
        response = await client.get("/api/v1/reports/", headers=auth_headers)
        assert response.status_code == 200

    async def test_user_cannot_generate_reports(
        self,
        client: AsyncClient,
        auth_headers: dict,  # Regular user (no REPORTS_GENERATE)
    ):
        """User without REPORTS_GENERATE should get 403."""
        response = await client.post("/api/v1/reports/generate", headers=auth_headers)
        assert response.status_code == 403

    async def test_admin_can_generate_reports(
        self,
        client: AsyncClient,
        admin_auth_headers: dict,
    ):
        """Admin should generate reports."""
        response = await client.post("/api/v1/reports/generate", headers=admin_auth_headers)
        assert response.status_code == 200
```

## Checklist

- [ ] Permission added to `Permission` enum
- [ ] Permission assigned to roles in `ROLE_PERMISSIONS`
- [ ] Schema patterns updated (if new roles)
- [ ] Endpoint uses `require_permissions()` or `require_any_permission()`
- [ ] Service layer checks permissions where needed
- [ ] Tests verify permission enforcement
