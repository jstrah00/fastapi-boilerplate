"""
Feed and post endpoints for the A2W platform.

Handles post CRUD, likes, and comments for the social feed.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import CurrentUser
from app.common.exceptions import NotFoundError, ValidationError
from app.common.logging import get_logger
from app.common.permissions import Permission, require_permissions
from app.schemas.post import (
    PostCreate,
    PostUpdate,
    PostResponse,
    PostListResponse,
    CommentCreate,
    CommentResponse,
    CommentListResponse,
    LikeToggleResponse,
    LikerResponse,
)
from app.services.post_service import PostService
from app.repositories.post_repo import PostRepository
from app.repositories.comment_repo import CommentRepository
from app.repositories.post_like_repo import PostLikeRepository
from app.repositories.user_repo import UserRepository
from app.repositories.notification_repo import NotificationRepository
from app.services.notification_service import NotificationService
from app.db.postgres import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from fastapi import Depends as _Depends

logger = get_logger(__name__)

router = APIRouter(prefix="/posts", tags=["feed"])


# --------------------------------------------------------------------- #
# Dependency
# --------------------------------------------------------------------- #

async def get_post_service(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> PostService:
    """Build PostService with all repositories."""
    post_repo = PostRepository(db)
    comment_repo = CommentRepository(db)
    like_repo = PostLikeRepository(db)
    user_repo = UserRepository(db)
    notif_repo = NotificationRepository(db)
    notif_svc = NotificationService(notif_repo)
    return PostService(post_repo, comment_repo, like_repo, user_repo, notif_svc)


PostSvc = Annotated[PostService, Depends(get_post_service)]


# --------------------------------------------------------------------- #
# Feed
# --------------------------------------------------------------------- #

@router.get("", response_model=PostListResponse, summary="Get feed")
async def get_feed(
    current_user: CurrentUser,
    post_service: PostSvc,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> PostListResponse:
    """Get the chronological feed of posts."""
    return await post_service.get_feed(current_user, skip, limit)


@router.post(
    "",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create post",
)
async def create_post(
    data: PostCreate,
    current_user: CurrentUser,
    post_service: PostSvc,
) -> PostResponse:
    """Create a new feed post."""
    return await post_service.create_post(data, current_user)


@router.get("/{post_id}", response_model=PostResponse, summary="Get post")
async def get_post(
    post_id: UUID,
    current_user: CurrentUser,
    post_service: PostSvc,
) -> PostResponse:
    """Get a single post by ID."""
    try:
        return await post_service.get_post(post_id, current_user)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.get(
    "/user/{user_id}",
    response_model=PostListResponse,
    summary="Get user posts",
)
async def get_user_posts(
    user_id: UUID,
    current_user: CurrentUser,
    post_service: PostSvc,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> PostListResponse:
    """Get posts by a specific user (for public profile view)."""
    return await post_service.get_user_posts(user_id, current_user, skip, limit)


@router.patch("/{post_id}", response_model=PostResponse, summary="Update post")
async def update_post(
    post_id: UUID,
    data: PostUpdate,
    current_user: CurrentUser,
    post_service: PostSvc,
) -> PostResponse:
    """Update own post."""
    try:
        return await post_service.update_post(post_id, data, current_user)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)


@router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete post",
)
async def delete_post(
    post_id: UUID,
    current_user: CurrentUser,
    post_service: PostSvc,
) -> None:
    """Delete own post."""
    try:
        await post_service.delete_post(post_id, current_user)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)


# --------------------------------------------------------------------- #
# Likes
# --------------------------------------------------------------------- #

@router.post(
    "/{post_id}/like",
    response_model=LikeToggleResponse,
    summary="Toggle like",
)
async def toggle_like(
    post_id: UUID,
    current_user: CurrentUser,
    post_service: PostSvc,
) -> LikeToggleResponse:
    """Like or unlike a post."""
    try:
        return await post_service.toggle_like(post_id, current_user)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.get(
    "/{post_id}/likes",
    response_model=list[LikerResponse],
    summary="Get likers",
)
async def get_likers(
    post_id: UUID,
    current_user: CurrentUser,
    post_service: PostSvc,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> list[LikerResponse]:
    """Get the list of users who liked a post."""
    try:
        return await post_service.get_likers(post_id, skip, limit)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


# --------------------------------------------------------------------- #
# Comments
# --------------------------------------------------------------------- #

@router.get(
    "/{post_id}/comments",
    response_model=CommentListResponse,
    summary="Get comments",
)
async def get_comments(
    post_id: UUID,
    current_user: CurrentUser,
    post_service: PostSvc,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> CommentListResponse:
    """Get comments for a post."""
    try:
        return await post_service.get_comments(post_id, skip, limit)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.post(
    "/{post_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add comment",
)
async def add_comment(
    post_id: UUID,
    data: CommentCreate,
    current_user: CurrentUser,
    post_service: PostSvc,
) -> CommentResponse:
    """Add a comment to a post."""
    try:
        return await post_service.add_comment(post_id, data, current_user)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)


@router.delete(
    "/{post_id}/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete comment",
)
async def delete_comment(
    post_id: UUID,
    comment_id: UUID,
    current_user: CurrentUser,
    post_service: PostSvc,
) -> None:
    """Delete own comment."""
    try:
        await post_service.delete_comment(post_id, comment_id, current_user)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)
