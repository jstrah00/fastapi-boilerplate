-- =============================================================================
-- PostgreSQL Initialization Script
--
-- This script runs automatically when the PostgreSQL container starts.
-- Add any database extensions or initial configuration here.
--
-- NOTE: Tables are created by Alembic migrations, not this script.
-- =============================================================================

-- Useful extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";     -- UUID generation
CREATE EXTENSION IF NOT EXISTS "pg_trgm";       -- Text search (trigrams)
CREATE EXTENSION IF NOT EXISTS "unaccent";      -- Remove accents from text

-- CUSTOMIZATION: Add any additional extensions your project needs:
-- CREATE EXTENSION IF NOT EXISTS "postgis";    -- Geospatial data
-- CREATE EXTENSION IF NOT EXISTS "hstore";     -- Key-value pairs
-- CREATE EXTENSION IF NOT EXISTS "ltree";      -- Hierarchical data
