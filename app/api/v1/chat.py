"""
Chat API endpoints for Stream Chat integration.

Provides token generation for authenticated users to connect to Stream Chat.
Stream handles all message storage, real-time delivery, and chat infrastructure.

Key components:
    - POST /chat/token: Get Stream Chat token for current user

Dependencies:
    - stream_chat: Stream Chat Python SDK
    - app.config: STREAM_API_KEY, STREAM_API_SECRET
    - app.api.deps: CurrentUser dependency

Related files:
    - app/schemas/chat.py: ChatTokenResponse schema
    - app/config.py: Stream configuration

Common commands:
    - Try: http://localhost:8000/docs#/chat

Example:
    Get chat token::

        curl -X POST http://localhost:8000/api/v1/chat/token \\
            -H "Authorization: Bearer eyJ..."

        # Response: {"token": "eyJ...", "api_key": "your_key"}
"""

from fastapi import APIRouter, HTTPException, status
from stream_chat import StreamChat

from app.api.deps import CurrentUser, UserRepo
from app.config import settings
from app.common.logging import get_logger
from app.schemas.chat import ChatTokenResponse, ChatUser

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post(
    "/token",
    response_model=ChatTokenResponse,
    summary="Get Stream Chat token",
    description="Generate a Stream Chat token for the authenticated user. "
    "Also creates/updates the user in Stream Chat.",
)
async def get_chat_token(
    current_user: CurrentUser,
) -> ChatTokenResponse:
    """Get Stream Chat token for current user."""
    if not settings.STREAM_API_KEY or not settings.STREAM_API_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chat service is not configured",
        )

    user_id = str(current_user.id)

    logger.info("chat_token_requested", user_id=user_id)

    client = StreamChat(
        api_key=settings.STREAM_API_KEY,
        api_secret=settings.STREAM_API_SECRET,
    )

    # Upsert user to Stream Chat
    client.upsert_user({
        "id": user_id,
        "name": current_user.full_name,
        "role": "user",
    })

    # Generate token
    token: str = client.create_token(user_id)

    logger.info("chat_token_generated", user_id=user_id)

    return ChatTokenResponse(token=token, api_key=settings.STREAM_API_KEY)


@router.get(
    "/users",
    response_model=list[ChatUser],
    summary="List users available for chat",
    description="Returns active users that can be messaged. Available to any authenticated user.",
)
async def list_chat_users(
    current_user: CurrentUser,
    user_repo: UserRepo,
) -> list[ChatUser]:
    """List active users for the chat user picker."""
    users = await user_repo.get_active_users(skip=0, limit=100)
    return [
        ChatUser(
            id=str(u.id),
            first_name=u.first_name,
            last_name=u.last_name,
            email=u.email,
        )
        for u in users
        if u.id != current_user.id
    ]
