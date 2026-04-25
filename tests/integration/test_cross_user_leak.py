"""
Regression test: a user must not be able to read items owned by another user.

This guards the per-user ownership boundary that the project relies on while
the multi-tenant Organization model is not yet implemented (CRITICAL-1 in
docs/audits/claude-setup-audit-2026-04-25.md). When Organization lands, this
test should be widened to cross-tenant.
"""

from __future__ import annotations

from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.security import get_password_hash


@pytest.fixture
async def user_b_data() -> dict[str, Any]:
    return {
        "email": "user-b@example.com",
        "first_name": "User",
        "last_name": "Bravo",
        "password": "userBpassword123",
        "role": "user",
    }


@pytest.fixture
async def user_b(db_session: AsyncSession, user_b_data: dict[str, Any]) -> Any:
    from app.models.postgres.user import User

    user = User(
        email=user_b_data["email"],
        first_name=user_b_data["first_name"],
        last_name=user_b_data["last_name"],
        password_hash=get_password_hash(user_b_data["password"]),
        role=user_b_data["role"],
        status="active",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def item_owned_by_user_b(db_session: AsyncSession, user_b: Any) -> Any:
    from app.models.postgres.item import Item

    item = Item(
        title="User B's private item",
        description="Should never be visible to anyone but B (or admin).",
        owner_id=user_b.id,
        status="active",
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item


@pytest.mark.asyncio
async def test_user_a_cannot_read_user_b_item(
    client: AsyncClient,
    auth_headers: dict[str, str],
    item_owned_by_user_b: Any,
) -> None:
    """User A (auth_headers fixture) must not see an item owned by user B."""
    response = await client.get(
        f"/api/v1/items/{item_owned_by_user_b.id}",
        headers=auth_headers,
    )
    assert response.status_code in (403, 404), (
        f"cross-user leak: user A received {response.status_code} when reading "
        f"item owned by user B (expected 403 or 404). Body: {response.text}"
    )


@pytest.mark.asyncio
async def test_user_a_cannot_update_user_b_item(
    client: AsyncClient,
    auth_headers: dict[str, str],
    item_owned_by_user_b: Any,
) -> None:
    """User A must not be able to update an item owned by user B."""
    response = await client.patch(
        f"/api/v1/items/{item_owned_by_user_b.id}",
        headers=auth_headers,
        json={"title": "hijacked"},
    )
    assert response.status_code in (403, 404), (
        f"cross-user write leak: user A received {response.status_code} when "
        f"updating item owned by user B. Body: {response.text}"
    )


@pytest.mark.asyncio
async def test_user_a_cannot_delete_user_b_item(
    client: AsyncClient,
    auth_headers: dict[str, str],
    item_owned_by_user_b: Any,
) -> None:
    """User A must not be able to delete an item owned by user B."""
    response = await client.delete(
        f"/api/v1/items/{item_owned_by_user_b.id}",
        headers=auth_headers,
    )
    assert response.status_code in (403, 404), (
        f"cross-user delete leak: user A received {response.status_code} when "
        f"deleting item owned by user B. Body: {response.text}"
    )
