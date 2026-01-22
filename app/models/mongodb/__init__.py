"""
Beanie document models for MongoDB.

Contains all document models using Beanie ODM for flexible schema storage.
Documents are registered during init_mongodb() in app.db.mongodb.

Key components:
    - ExampleDocument: Example document model with flexible schema

Dependencies:
    - beanie: Async ODM for MongoDB
    - pydantic: Data validation

Related files:
    - app/db/mongodb.py: Register documents in init_beanie()

Common commands:
    - Start MongoDB: docker compose up -d mongodb
    - Mongo Express: http://localhost:8081 (with --profile tools)

Example:
    Import documents::

        from app.models.mongodb import ExampleDocument
        # or
        from app.models.mongodb.document import ExampleDocument

Note:
    When creating new documents, register them in app/db/mongodb.py
    init_mongodb() function's document_models list.
    If not using MongoDB, this folder can be safely deleted.
"""
from app.models.mongodb.document import ExampleDocument

__all__ = [
    "ExampleDocument",
]
