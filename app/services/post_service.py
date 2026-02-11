"""
Post service handling feed, comments, likes, and @mention parsing.
"""
import re
from uuid import UUID

from app.models.postgres.post import Post
from app.models.postgres.comment import Comment
from app.models.postgres.post_like import PostLike
from app.models.postgres.user import User
from app.repositories.post_repo import PostRepository
from app.repositories.comment_repo import CommentRepository
from app.repositories.post_like_repo import PostLikeRepository
from app.repositories.user_repo import UserRepository
from app.services.notification_service import NotificationService
from app.services import email_service
from app.schemas.post import (
    PostCreate,
    PostUpdate,
    PostResponse,
    PostListResponse,
    PostAuthor,
    CommentCreate,
    CommentResponse,
    CommentListResponse,
    LikeToggleResponse,
    LikerResponse,
)
from app.common.exceptions import NotFoundError, ValidationError
from app.common.logging import get_logger

logger = get_logger(__name__)

# Matches @[Name](user_id) pattern used for mentions
MENTION_PATTERN = re.compile(r"@\[([^\]]+)\]\(([0-9a-fA-F\-]{36})\)")


def _author_from_user(user: User) -> PostAuthor:
    """Build PostAuthor from a User model."""
    return PostAuthor(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        avatar_url=user.avatar_url,
        role=user.role,
    )


class PostService:
    """Service for feed posts, comments, and likes."""

    def __init__(
        self,
        post_repo: PostRepository,
        comment_repo: CommentRepository,
        like_repo: PostLikeRepository,
        user_repo: UserRepository,
        notification_service: NotificationService,
    ):
        self.post_repo = post_repo
        self.comment_repo = comment_repo
        self.like_repo = like_repo
        self.user_repo = user_repo
        self.notification_service = notification_service

    # --------------------------------------------------------------------- #
    # Feed
    # --------------------------------------------------------------------- #

    async def get_feed(
        self, current_user: User, skip: int = 0, limit: int = 20
    ) -> PostListResponse:
        """Get the chronological feed."""
        posts = await self.post_repo.get_feed(skip, limit)
        total = await self.post_repo.count_feed()
        liked_ids = await self.like_repo.get_liked_post_ids(
            current_user.id, [p.id for p in posts]
        )
        return PostListResponse(
            posts=[self._post_response(p, p.id in liked_ids) for p in posts],
            total=total,
        )

    async def get_post(self, post_id: UUID, current_user: User) -> PostResponse:
        """Get a single post."""
        post = await self.post_repo.get(post_id)
        if not post or post.is_hidden:
            raise NotFoundError(message="Post not found")
        liked_ids = await self.like_repo.get_liked_post_ids(
            current_user.id, [post.id]
        )
        return self._post_response(post, post.id in liked_ids)

    async def get_user_posts(
        self, author_id: UUID, current_user: User, skip: int = 0, limit: int = 20
    ) -> PostListResponse:
        """Get posts by a specific user (for public profile)."""
        posts = await self.post_repo.get_by_author(author_id, skip, limit)
        total = await self.post_repo.count_by_author(author_id)
        liked_ids = await self.like_repo.get_liked_post_ids(
            current_user.id, [p.id for p in posts]
        )
        return PostListResponse(
            posts=[self._post_response(p, p.id in liked_ids) for p in posts],
            total=total,
        )

    # --------------------------------------------------------------------- #
    # Post CRUD
    # --------------------------------------------------------------------- #

    async def create_post(self, data: PostCreate, author: User) -> PostResponse:
        """Create a new post and notify mentioned users."""
        post = Post(author_id=author.id, content=data.content)
        post = await self.post_repo.create(post)
        # Reload to get author relationship
        post = await self.post_repo.get(post.id)

        # Parse @mentions and notify
        await self._process_mentions(data.content, author, post.id)

        logger.info("post_created", post_id=str(post.id), author=str(author.id))
        return self._post_response(post, False)

    async def update_post(
        self, post_id: UUID, data: PostUpdate, current_user: User
    ) -> PostResponse:
        """Update own post (or admin can update any)."""
        post = await self._get_post_or_404(post_id)
        if post.author_id != current_user.id and not current_user.is_admin:
            raise ValidationError(message="You can only edit your own posts")
        post = await self.post_repo.update(post_id, {"content": data.content})
        liked_ids = await self.like_repo.get_liked_post_ids(
            current_user.id, [post.id]
        )
        return self._post_response(post, post.id in liked_ids)

    async def delete_post(self, post_id: UUID, current_user: User) -> None:
        """Delete own post (or admin can delete any)."""
        post = await self._get_post_or_404(post_id)
        if post.author_id != current_user.id and not current_user.is_admin:
            raise ValidationError(message="You can only delete your own posts")
        await self.post_repo.delete(post_id)
        logger.info("post_deleted", post_id=str(post_id), by=str(current_user.id))

    # --------------------------------------------------------------------- #
    # Likes
    # --------------------------------------------------------------------- #

    async def toggle_like(self, post_id: UUID, user: User) -> LikeToggleResponse:
        """Toggle like on a post."""
        post = await self._get_post_or_404(post_id)
        existing = await self.like_repo.get_by_post_and_user(post_id, user.id)

        if existing:
            await self.like_repo.delete_by_post_and_user(post_id, user.id)
            new_count = max(0, post.likes_count - 1)
            await self.post_repo.update(post_id, {"likes_count": new_count})
            return LikeToggleResponse(liked=False, likes_count=new_count)
        else:
            like = PostLike(post_id=post_id, user_id=user.id)
            await self.like_repo.create(like)
            new_count = post.likes_count + 1
            await self.post_repo.update(post_id, {"likes_count": new_count})
            await self.notification_service.create_notification(
                user_id=post.author_id,
                actor_id=user.id,
                notification_type="like",
                post_id=post_id,
            )
            # Send email notification if recipient has it enabled
            if post.author_id != user.id:
                post_author = await self.user_repo.get(post.author_id)
                if post_author and post_author.email_notifications_enabled:
                    await email_service.send_notification_like(
                        post_author.email, post_author.first_name, user.full_name
                    )
            return LikeToggleResponse(liked=True, likes_count=new_count)

    async def get_likers(
        self, post_id: UUID, skip: int = 0, limit: int = 50
    ) -> list[LikerResponse]:
        """Get users who liked a post."""
        await self._get_post_or_404(post_id)
        likes = await self.like_repo.get_likers(post_id, skip, limit)
        return [
            LikerResponse(
                id=like.user.id,
                first_name=like.user.first_name,
                last_name=like.user.last_name,
                avatar_url=like.user.avatar_url,
                role=like.user.role,
            )
            for like in likes
        ]

    # --------------------------------------------------------------------- #
    # Comments
    # --------------------------------------------------------------------- #

    async def get_comments(
        self, post_id: UUID, skip: int = 0, limit: int = 50
    ) -> CommentListResponse:
        """Get comments for a post."""
        await self._get_post_or_404(post_id)
        comments = await self.comment_repo.get_by_post(post_id, skip, limit)
        total = await self.comment_repo.count_by_post(post_id)
        return CommentListResponse(
            comments=[
                CommentResponse(
                    id=c.id,
                    post_id=c.post_id,
                    author=_author_from_user(c.author),
                    content=c.content,
                    created_at=c.created_at,
                )
                for c in comments
            ],
            total=total,
        )

    async def add_comment(
        self, post_id: UUID, data: CommentCreate, user: User
    ) -> CommentResponse:
        """Add a comment to a post."""
        post = await self._get_post_or_404(post_id)
        comment = Comment(
            post_id=post_id, author_id=user.id, content=data.content
        )
        comment = await self.comment_repo.create(comment)
        # Reload for author relationship
        comment = await self.comment_repo.get(comment.id)

        # Increment counter
        await self.post_repo.update(
            post_id, {"comments_count": post.comments_count + 1}
        )

        # Notify post author
        await self.notification_service.create_notification(
            user_id=post.author_id,
            actor_id=user.id,
            notification_type="comment",
            post_id=post_id,
            comment_id=comment.id,
        )

        # Send email notification if recipient has it enabled
        if post.author_id != user.id:
            post_author = await self.user_repo.get(post.author_id)
            if post_author and post_author.email_notifications_enabled:
                await email_service.send_notification_comment(
                    post_author.email, post_author.first_name, user.full_name
                )

        return CommentResponse(
            id=comment.id,
            post_id=comment.post_id,
            author=_author_from_user(comment.author),
            content=comment.content,
            created_at=comment.created_at,
        )

    async def delete_comment(
        self, post_id: UUID, comment_id: UUID, current_user: User
    ) -> None:
        """Delete own comment (or admin can delete any)."""
        comment = await self.comment_repo.get(comment_id)
        if not comment or comment.post_id != post_id:
            raise NotFoundError(message="Comment not found")
        if comment.author_id != current_user.id and not current_user.is_admin:
            raise ValidationError(message="You can only delete your own comments")

        await self.comment_repo.delete(comment_id)

        # Decrement counter
        post = await self.post_repo.get(post_id)
        if post:
            await self.post_repo.update(
                post_id, {"comments_count": max(0, post.comments_count - 1)}
            )

    # --------------------------------------------------------------------- #
    # Helpers
    # --------------------------------------------------------------------- #

    async def toggle_post_visibility(self, post_id: UUID) -> None:
        """Toggle is_hidden on a post (admin moderation)."""
        post = await self.post_repo.get(post_id)
        if not post:
            raise NotFoundError(message="Post not found")
        await self.post_repo.update(post_id, {"is_hidden": not post.is_hidden})
        logger.info("post_visibility_toggled", post_id=str(post_id), hidden=not post.is_hidden)

    async def toggle_comment_visibility(self, comment_id: UUID) -> None:
        """Toggle is_hidden on a comment (admin moderation)."""
        comment = await self.comment_repo.get(comment_id)
        if not comment:
            raise NotFoundError(message="Comment not found")
        await self.comment_repo.update(comment_id, {"is_hidden": not comment.is_hidden})
        logger.info("comment_visibility_toggled", comment_id=str(comment_id), hidden=not comment.is_hidden)

    async def _get_post_or_404(self, post_id: UUID) -> Post:
        """Fetch post or raise NotFoundError."""
        post = await self.post_repo.get(post_id)
        if not post or post.is_hidden:
            raise NotFoundError(message="Post not found")
        return post

    def _post_response(self, post: Post, is_liked: bool) -> PostResponse:
        """Build PostResponse from Post model."""
        return PostResponse(
            id=post.id,
            author=_author_from_user(post.author),
            content=post.content,
            likes_count=post.likes_count,
            comments_count=post.comments_count,
            is_liked=is_liked,
            created_at=post.created_at,
            updated_at=post.updated_at,
        )

    async def _process_mentions(
        self, content: str, author: User, post_id: UUID
    ) -> None:
        """Parse @[Name](uuid) mentions and create notifications."""
        for _name, user_id_str in MENTION_PATTERN.findall(content):
            try:
                mentioned_id = UUID(user_id_str)
                user = await self.user_repo.get(mentioned_id)
                if user and user.is_active:
                    await self.notification_service.create_notification(
                        user_id=mentioned_id,
                        actor_id=author.id,
                        notification_type="mention",
                        post_id=post_id,
                    )
            except ValueError:
                continue
