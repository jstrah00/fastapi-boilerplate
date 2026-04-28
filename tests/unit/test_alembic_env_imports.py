"""
Unit tests guarding alembic/env.py model registration.

Alembic autogenerate only sees models whose modules have been imported into
the SQLAlchemy metadata at the time `alembic revision --autogenerate` runs.
That import side-effect is triggered by a single line in alembic/env.py
(today: `from app.models.postgres import user, item, refresh_token_blacklist`).
If a new model module is added under app/models/postgres/ but the developer
forgets to update env.py, autogenerate silently emits an empty migration —
the table never reaches prod.

This test enforces parity: every non-private module under app.models.postgres
must be referenced inside alembic/env.py. Closes NEW-CRIT-A in
saas-boilerplate/docs/audits/claude-setup-audit-2026-04-28.md.
"""

from __future__ import annotations

import pkgutil
from pathlib import Path

import app.models.postgres as postgres_models_pkg


def _alembic_env_text() -> str:
    """Read alembic/env.py from disk, anchored at the backend repo root."""
    repo_root = Path(__file__).resolve().parents[2]
    env_path = repo_root / "alembic" / "env.py"
    return env_path.read_text(encoding="utf-8")


def _postgres_model_modules() -> list[str]:
    """Return submodule names under app.models.postgres (e.g. 'user', 'item')."""
    return [
        modinfo.name
        for modinfo in pkgutil.iter_modules(postgres_models_pkg.__path__)
        if not modinfo.name.startswith("_")
    ]


def test_alembic_env_imports_every_postgres_model() -> None:
    """Every postgres model module must appear in alembic/env.py's import list."""
    env_source = _alembic_env_text()
    modules = _postgres_model_modules()

    assert modules, "Discovered no postgres model modules — test setup is broken."

    missing = [name for name in modules if name not in env_source]
    assert not missing, (
        "alembic/env.py is missing imports for these postgres model modules: "
        f"{missing}. Without them, `alembic revision --autogenerate` cannot see "
        "their tables and will silently produce empty migrations. Add each name "
        "to the `from app.models.postgres import ...` line in alembic/env.py."
    )


def test_alembic_env_imports_known_models_explicitly() -> None:
    """Pin the three currently-shipping models so a rename or removal trips the test."""
    env_source = _alembic_env_text()
    for required in ("user", "item", "refresh_token_blacklist"):
        assert required in env_source, (
            f"alembic/env.py no longer references the `{required}` model module. "
            "If it was renamed, update this assertion and the env.py import in the "
            "same commit so future autogenerate runs still see the table."
        )
