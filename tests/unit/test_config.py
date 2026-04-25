"""
Unit tests for application settings validation.

Regression guard for the production SECRET_KEY check (CRITICAL-2 in
docs/audits/claude-setup-audit-2026-04-25.md): when ENVIRONMENT=production,
SECRET_KEY must NOT be a placeholder starting with "dev-secret-key-".
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

REQUIRED_ENV: dict[str, str] = {
    "POSTGRES_SERVER": "localhost",
    "POSTGRES_USER": "app_user",
    "POSTGRES_PASSWORD": "app_dev_password",
    "POSTGRES_DB": "app_db",
    "MONGODB_URL": "mongodb://localhost:27017",
    "MONGODB_DB": "app_db",
}


def _set_required_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in REQUIRED_ENV.items():
        monkeypatch.setenv(key, value)


class TestSecretKeyValidator:
    """Validator: dev-* SECRET_KEY must be rejected when ENVIRONMENT=production."""

    def test_dev_secret_key_rejected_in_production(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _set_required_env(monkeypatch)
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv(
            "SECRET_KEY",
            "dev-secret-key-change-in-production-use-openssl-rand-hex-32",
        )

        from app.config import Settings

        with pytest.raises(ValidationError) as exc_info:
            Settings(_env_file=None)  # type: ignore[call-arg]

        assert "SECRET_KEY" in str(exc_info.value)

    def test_dev_secret_key_allowed_in_development(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _set_required_env(monkeypatch)
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv(
            "SECRET_KEY",
            "dev-secret-key-change-in-production-use-openssl-rand-hex-32",
        )

        from app.config import Settings

        settings = Settings(_env_file=None)  # type: ignore[call-arg]
        assert settings.SECRET_KEY.startswith("dev-secret-key-")

    def test_real_secret_key_allowed_in_production(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _set_required_env(monkeypatch)
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv(
            "SECRET_KEY",
            "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
        )

        from app.config import Settings

        settings = Settings(_env_file=None)  # type: ignore[call-arg]
        assert settings.is_production is True
