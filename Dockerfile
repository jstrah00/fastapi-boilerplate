# Production multi-stage Dockerfile for A2W Backend
FROM python:3.12-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install UV
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install production dependencies only
RUN uv sync --no-dev

# Copy application code
COPY . .

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser -d /app appuser \
    && mkdir -p /app/uploads && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Default command - can be overridden in docker-compose
CMD ["uv", "run", "gunicorn", "app.main:app", "-c", "gunicorn.conf.py"]
