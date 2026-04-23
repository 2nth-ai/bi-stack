#!/usr/bin/env bash
# One-shot bootstrap — idempotent. Runs migrations, creates the admin user,
# and loads built-in roles. Safe to run on every startup.
set -euo pipefail

echo "[bootstrap] upgrading Superset metadata schema"
superset db upgrade

echo "[bootstrap] initialising default roles and permissions"
superset init

echo "[bootstrap] ensuring admin user exists"
superset fab create-admin \
  --username "${ADMIN_USERNAME:-admin}" \
  --firstname "${ADMIN_FIRSTNAME:-Admin}" \
  --lastname "${ADMIN_LASTNAME:-User}" \
  --email "${ADMIN_EMAIL:-admin@2nth.ai}" \
  --password "${ADMIN_PASSWORD:?ADMIN_PASSWORD required}" \
  || echo "[bootstrap] admin user already exists — skipping"

echo "[bootstrap] done"
