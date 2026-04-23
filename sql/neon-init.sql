-- One-time schema setup for the Neon database.
-- Run once per Neon branch against the DIRECT (unpooled) endpoint:
--
--   psql "$ANALYTICS_DB_URI" -f sql/neon-init.sql
--
-- Idempotent — safe to re-run.

-- Superset stores its own tables (dashboards, charts, users, etc.) here.
CREATE SCHEMA IF NOT EXISTS superset_meta;

-- dbt writes staging views + mart tables here.
CREATE SCHEMA IF NOT EXISTS analytics;

-- Sanity check
SELECT nspname FROM pg_namespace WHERE nspname IN ('superset_meta', 'analytics');
