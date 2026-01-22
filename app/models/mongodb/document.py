"""
Example Document model for MongoDB using Beanie ODM.

Demonstrates how to create MongoDB documents with Beanie, featuring flexible
schemas, nested data, and cross-database references.

Key components:
    - ExampleDocument: Beanie Document model with flexible schema
    - data: Dict field for arbitrary JSON (no migrations needed)
    - tags: List field demonstrating array storage
    - owner_id: String reference to PostgreSQL user (cross-DB)
    - Settings: Beanie configuration for collection name and indexes

Dependencies:
    - beanie: Async ODM for MongoDB
    - pydantic: Data validation (Beanie uses Pydantic)
    - app.db.mongodb: Database initialization

Related files:
    - app/db/mongodb.py: init_mongodb() registers this document
    - app/config.py: MongoDB connection settings

Common commands:
    - Start MongoDB: docker compose up -d mongodb
    - Mongo shell: docker compose exec mongodb mongosh

Example:
    Creating a document::

        from app.models.mongodb.document import ExampleDocument

        doc = ExampleDocument(
            name="My Document",
            description="Description here",
            data={"nested": {"key": "value"}, "count": 42},
            tags=["tag1", "tag2"],
            owner_id=str(user.id),  # Cross-DB reference as string
        )
        await doc.insert()

    Querying documents::

        # Find by field
        docs = await ExampleDocument.find(
            ExampleDocument.status == "active"
        ).to_list()

        # Find one
        doc = await ExampleDocument.find_one(
            ExampleDocument.name == "My Document"
        )

        # Update
        doc.data["count"] = 100
        await doc.save()

When to use MongoDB vs PostgreSQL:
    - MongoDB: Flexible/evolving schemas, nested data, document storage
    - PostgreSQL: Strict schemas, relationships, complex queries, transactions
"""
from datetime import datetime, UTC
from typing import Any

from beanie import Document
from pydantic import Field


class ExampleDocument(Document):
    """
    Example MongoDB document model.

    # EXAMPLE: This shows a flexible document structure.
    # MongoDB documents can have nested objects and arrays without migrations.
    #
    # When to use MongoDB vs PostgreSQL:
    # - MongoDB: Flexible/evolving schemas, nested data, document storage
    # - PostgreSQL: Strict schemas, relationships, complex queries, transactions
    """

    # Document fields
    name: str = Field(index=True)
    description: str | None = None

    # Flexible data field - can store any JSON structure
    # This is where MongoDB shines - no schema migrations needed
    data: dict[str, Any] = Field(default_factory=dict)

    # Tags example - arrays are natural in MongoDB
    tags: list[str] = Field(default_factory=list)

    # Status for filtering
    status: str = Field(default="active", index=True)

    # Owner reference (store PostgreSQL user ID as string)
    # NOTE: Cross-database references are stored as strings
    owner_id: str | None = Field(default=None, index=True)

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        # Collection name in MongoDB
        name = "documents"
        # Indexes for common queries
        indexes = [
            "name",
            "status",
            "owner_id",
            "created_at",
            [("created_at", -1)],  # Descending for recent-first queries
        ]

    def __repr__(self) -> str:
        return f"<ExampleDocument {self.name}>"

    def to_dict(self) -> dict[str, Any]:
        """Convert document to dictionary for API responses."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "data": self.data,
            "tags": self.tags,
            "status": self.status,
            "owner_id": self.owner_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
