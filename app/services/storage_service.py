"""
File storage service with pluggable backends.

Supports local filesystem (development) and AWS S3 (production).
Configured via STORAGE_PROVIDER environment variable.

Usage:
    storage = get_storage_service()
    url = await storage.upload_avatar(file, user_id)
"""
import os
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.config import settings
from app.common.logging import get_logger
from app.common.exceptions import ValidationError

logger = get_logger(__name__)

MAX_IMAGE_SIZE = 1 * 1024 * 1024  # 1MB
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
UPLOADS_DIR = Path("uploads")


class LocalStorageService:
    """Store files on the local filesystem (development)."""

    def __init__(self, base_dir: Path = UPLOADS_DIR) -> None:
        """Initialize local storage and ensure directories exist."""
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        (self.base_dir / "avatars").mkdir(exist_ok=True)

    async def upload_avatar(self, file: UploadFile, user_id: str) -> str:
        """Upload a profile image and return its URL path."""
        self._validate_image(file)

        ext = self._get_extension(file.filename or "image.jpg")
        filename = f"{user_id}_{uuid.uuid4().hex[:8]}{ext}"
        file_path = self.base_dir / "avatars" / filename

        content = await file.read()
        if len(content) > MAX_IMAGE_SIZE:
            raise ValidationError(
                message="Image exceeds maximum size of 1MB",
                details={"max_size": "1MB"},
            )

        with open(file_path, "wb") as f:
            f.write(content)

        url = f"/uploads/avatars/{filename}"
        logger.info("avatar_uploaded", user_id=user_id, path=url)
        return url

    async def delete_file(self, url: str) -> None:
        """Delete a file by its URL path."""
        if not url or not url.startswith("/uploads/"):
            return
        file_path = Path(url.lstrip("/"))
        if file_path.exists():
            os.remove(file_path)
            logger.info("file_deleted", path=url)

    def _validate_image(self, file: UploadFile) -> None:
        """Validate file is an allowed image type."""
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise ValidationError(
                message=f"Invalid image type: {file.content_type}. Allowed: JPEG, PNG, WebP",
                details={"allowed_types": list(ALLOWED_IMAGE_TYPES)},
            )

    def _get_extension(self, filename: str) -> str:
        """Extract file extension."""
        _, ext = os.path.splitext(filename)
        return ext.lower() if ext else ".jpg"


def get_storage_service() -> LocalStorageService:
    """Get the configured storage service instance."""
    # Future: check settings.STORAGE_PROVIDER for "s3" and return S3StorageService
    return LocalStorageService()
