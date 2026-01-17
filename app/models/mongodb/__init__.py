"""
MongoDB models using Beanie ODM.

# =============================================================================
# MODELS: Import your Beanie document models here.
# These will be initialized when MongoDB connects.
#
# NOTE ON DATABASE CHOICE:
# If your project only needs PostgreSQL, you can safely:
# 1. Delete this mongodb/ folder
# 2. Remove MongoDB dependencies from pyproject.toml (motor, beanie, pymongo)
# 3. Remove MongoDB service from docker-compose.yml
# 4. Remove MongoDB initialization from app/main.py
# 5. Remove app/db/mongodb.py
# =============================================================================
"""
from app.models.mongodb.document import ExampleDocument

__all__ = [
    "ExampleDocument",
]
