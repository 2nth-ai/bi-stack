#!/usr/bin/env bash
# Deploy/update the dbt Cloud Run Job. Triggered daily by scheduler.sh.
source "$(dirname "$0")/config.sh"

gcloud run jobs deploy bi-dbt-run \
  --project "${GCP_PROJECT}" \
  --region "${GCP_REGION}" \
  --image "${DBT_IMAGE}" \
  --service-account "${SA_RUNTIME}" \
  --task-timeout 1800 \
  --max-retries 2 \
  --cpu 1 \
  --memory 1Gi \
  --set-env-vars "DBT_PROFILES_DIR=/app" \
  --set-secrets "NEON_POOLED_URI=${SEC_NEON_POOLED}:latest"
