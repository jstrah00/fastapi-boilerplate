"""
Pydantic schemas for chat endpoints.

Defines response DTOs for Stream Chat token generation.

Key components:
    - ChatTokenResponse: Token and API key for Stream Chat initialization

Dependencies:
    - pydantic: Data validation and serialization

Related files:
    - app/api/v1/chat.py: Chat endpoints

Example:
    Token response::

        {
            "token": "eyJ...",
            "api_key": "your_stream_api_key"
        }
"""

from pydantic import BaseModel


class ChatTokenResponse(BaseModel):
    """Schema for Stream Chat token response."""

    token: str
    api_key: str


class ChatUser(BaseModel):
    """Minimal user info for chat user picker."""

    id: str
    first_name: str
    last_name: str
    email: str
