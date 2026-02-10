# Scripts

Database and utility scripts for the A2W backend. All commands assume you're at the **repository root**.

## init_db.py — Initialize Database

Creates tables, default admin user, and seeds master data (industries, professions, sport achievements).

```bash
# Via Docker (recommended)
docker compose exec backend uv run python scripts/init_db.py

# Locally (requires DB running)
cd backend && uv run python scripts/init_db.py
```

## seed_demo_data.py — Seed Demo Data

Populates the database with realistic demo data: 20 users (14 aretans + 6 contractors), 40 posts, comments, likes, and contact requests. Idempotent — skips if demo data already exists.

```bash
# Via Docker (recommended)
docker compose exec backend uv run python scripts/seed_demo_data.py

# Locally (requires DB running)
cd backend && uv run python scripts/seed_demo_data.py
```

All demo users share password: `Demo1234!`

## cli.py — Dev Server

Development server launcher with hot reload.

```bash
cd backend && uv run dev
```

## SQL / JS Init Scripts

- `init_postgres.sql` — Raw SQL for PostgreSQL initialization (used by Docker entrypoint)
- `init_mongo.js` — MongoDB initialization script (used by Docker entrypoint)
