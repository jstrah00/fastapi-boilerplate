"""CLI commands for the FastAPI application."""

import subprocess
import sys


def dev() -> None:
    """Run development server with hot reload."""
    subprocess.run(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--reload",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
        ],
        check=False,
    )


def test() -> None:
    """Run all tests with coverage."""
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--cov=app",
            "--cov-report=html",
            "--cov-report=term",
        ],
        check=False,
    )
