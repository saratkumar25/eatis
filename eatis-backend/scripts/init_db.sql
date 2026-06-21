-- scripts/init_db.sql
-- ─────────────────────────────────────────────────────────────────────────────
-- Runs automatically on first PostgreSQL container startup
-- (mounted to /docker-entrypoint-initdb.d/ in docker-compose.yml).
-- Table creation itself is handled by SQLAlchemy/Alembic at app startup;
-- this script only sets up extensions and DB-level configuration.
-- ─────────────────────────────────────────────────────────────────────────────

-- Useful for future geospatial queries (optional, safe no-op if unavailable)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Confirm timezone handling is consistent
SET timezone = 'UTC';
