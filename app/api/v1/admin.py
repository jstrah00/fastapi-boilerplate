"""
Admin dashboard and management endpoints.

Provides platform statistics and admin-only management operations.
"""
from fastapi import APIRouter

from app.api.deps import CurrentAdmin, UserRepo
from app.repositories.post_repo import PostRepository
from app.repositories.contact_request_repo import ContactRequestRepository
from app.db.postgres import get_db

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.common.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", summary="Get platform statistics")
async def get_platform_stats(
    current_user: CurrentAdmin,
    user_repo: UserRepo,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Get platform overview statistics. Admin only."""
    post_repo = PostRepository(db)
    contact_repo = ContactRequestRepository(db)

    # User counts
    total_users = await user_repo.count()
    active_users = await user_repo.count(filters={"status": "active"})
    pending_users = await user_repo.count(filters={"status": "pending"})
    blocked_users = await user_repo.count(filters={"status": "blocked"})
    aretan_count = await user_repo.count(filters={"role": "aretan"})
    contractor_count = await user_repo.count(filters={"role": "contratante"})

    # Post counts
    total_posts = await post_repo.count_feed()

    # Contact request counts
    pending_contacts = await contact_repo.count(filters={"status": "pending"})

    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "pending": pending_users,
            "blocked": blocked_users,
            "aretans": aretan_count,
            "contractors": contractor_count,
        },
        "posts": {
            "total": total_posts,
        },
        "contact_requests": {
            "pending": pending_contacts,
        },
    }
