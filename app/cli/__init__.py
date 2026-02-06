"""
CLI commands for maintenance and administration tasks.

Contains command-line utilities for database maintenance, cleanup,
and other operational tasks.

Key components:
    - blacklist: Cleanup expired refresh tokens

Dependencies:
    - asyncio: Async command execution
    - app.db.postgres: Database session
    - app.repositories: Data access layer

Related files:
    - pyproject.toml: Command registration for `uv run`

Common commands:
    - Cleanup blacklist: uv run cleanup-blacklist

Example:
    Running cleanup::

        # Manual cleanup
        uv run cleanup-blacklist

        # Check results
        psql -c "SELECT COUNT(*) FROM refresh_token_blacklist;"
"""
