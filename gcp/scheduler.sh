#!/usr/bin/env bash
# Cloud Scheduler cron — fires bi-dbt-run daily at 02:00 SAST.
# SAFEX closes 17:00 SAST; overnight run refreshes the warehouse.
source "$(dirname "$0")/config.sh"

JOB_URL="https://${GCP_REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${GCP_PROJECT}/jobs/bi-dbt-run:run"

gcloud scheduler jobs create http bi-dbt-daily \
  --project "${GCP_PROJECT}" \
  --location "${GCP_REGION}" \
  --schedule="0 2 * * *" \
  --time-zone="Africa/Johannesburg" \
  --uri="${JOB_URL}" \
  --http-method=POST \
  --oauth-service-account-email="${SA_RUNTIME}" \
  --description="Daily dbt build at 02:00 SAST" 2>/dev/null || \
gcloud scheduler jobs update http bi-dbt-daily \
  --project "${GCP_PROJECT}" \
  --location "${GCP_REGION}" \
  --schedule="0 2 * * *" \
  --time-zone="Africa/Johannesburg" \
  --uri="${JOB_URL}" \
  --http-method=POST \
  --oauth-service-account-email="${SA_RUNTIME}"
