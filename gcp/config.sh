#!/usr/bin/env bash
# Shared config for every gcp/*.sh script. Source this first.
# Fill in GCP_PROJECT locally once; everything else is derived.

set -euo pipefail

: "${GCP_PROJECT:?GCP_PROJECT env var required (e.g. export GCP_PROJECT=nth-bi-stack)}"
export GCP_REGION="${GCP_REGION:-africa-south1}"
export AR_REPO="${AR_REPO:-bi-stack}"
export AR_HOST="${GCP_REGION}-docker.pkg.dev"
export SUPERSET_IMAGE="${AR_HOST}/${GCP_PROJECT}/${AR_REPO}/superset:latest"
export DBT_IMAGE="${AR_HOST}/${GCP_PROJECT}/${AR_REPO}/dbt:latest"

export SA_RUNTIME="bi-stack-runtime@${GCP_PROJECT}.iam.gserviceaccount.com"
export SA_DEPLOYER="bi-stack-deployer@${GCP_PROJECT}.iam.gserviceaccount.com"

# Secret Manager secret names
export SEC_METADATA_URI="SUPERSET_METADATA_DB_URI"
export SEC_ANALYTICS_URI="ANALYTICS_DB_URI"
export SEC_NEON_POOLED="NEON_POOLED_URI"
export SEC_REDIS_URL="REDIS_URL"
export SEC_SUPERSET_KEY="SUPERSET_SECRET_KEY"
export SEC_GUEST_JWT="GUEST_TOKEN_JWT_SECRET"
export SEC_ADMIN_PW="ADMIN_PASSWORD"
export SEC_MAPBOX="MAPBOX_API_KEY"
