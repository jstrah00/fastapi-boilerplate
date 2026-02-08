"""
Schemas for feed posts, comments, and likes.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# Shared
# =============================================================================

class PostAuthor(BaseModel):
    """Minimal author info embedded in post/comment responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    first_name: str
    last_name: str
    avatar_url: str | None = None
    role: str


# =============================================================================
# Post
# =============================================================================

class PostCreate(BaseModel):
    """Schema for creating a post."""

    content: str = Field(min_length=1, max_length=5000)


class PostUpdate(BaseModel):
    """Schema for updating a post."""

    content: str = Field(min_length=1, max_length=5000)


class PostResponse(BaseModel):
    """Single post in the feed."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    author: PostAuthor
    content: str
    likes_count: int
    comments_count: int
    is_liked: bool = False
    created_at: datetime
    updated_at: datetime


class PostListResponse(BaseModel):
    """Paginated list of posts."""

    posts: list[PostResponse]
    total: int


# =============================================================================
# Comment
# =============================================================================

class CommentCreate(BaseModel):
    """Schema for adding a comment."""

    content: str = Field(min_length=1, max_length=2000)


class CommentResponse(BaseModel):
    """Single comment on a post."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    post_id: UUID
    author: PostAuthor
    content: str
    created_at: datetime


class CommentListResponse(BaseModel):
    """Paginated list of comments."""

    comments: list[CommentResponse]
    total: int


# =============================================================================
# Like
# =============================================================================

class LikeToggleResponse(BaseModel):
    """Response after toggling a like."""

    liked: bool
    likes_count: int


class LikerResponse(BaseModel):
    """User who liked a post."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    first_name: str
    last_name: str
    avatar_url: str | None = None
    role: str
