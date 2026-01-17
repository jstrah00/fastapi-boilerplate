"""
Data access repositories.

# =============================================================================
# REPOSITORY PATTERN: Abstracts database operations from business logic.
# Each model should have its own repository extending BaseRepository.
# =============================================================================
"""
from app.repositories.base import BaseRepository
from app.repositories.user_repo import UserRepository
from app.repositories.item_repo import ItemRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "ItemRepository",
]
