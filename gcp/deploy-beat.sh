#!/usr/bin/env bash
# Deploy Celery beat as a singleton service. Must be a service, not a Job:
# beat is a persistent loop; Cloud Run Jobs exit on completion.
source "$(dirname "$0")/config.sh"

gcloud run deploy bi-superset-beat \
  --project "${GCP_PROJECT}" \
  --region "${GCP_REGION}" \
  --image "${SUPERSET_IMAGE}" \
  --service-account "${SA_RUNTIME}" \
  --no-allow-unauthenticated \
  --cpu 1 \
  --memory 512Mi \
  --min-instances 1 \
  --max-instances 1 \
  --no-cpu-throttling \
  --command celery \
  --args='--app=superset.tasks.celery_app:app,beat,--loglevel=INFO' \
  --set-env-vars "SUPERSET_CONFIG_PATH=/app/pythonpath/superset_config.py" \
  --set-secrets "SUPERSET_METADATA_DB_URI=${SEC_METADATA_URI}:latest,REDIS_URL=${SEC_REDIS_URL}:latest,SUPERSET_SECRET_KEY=${SEC_SUPERSET_KEY}:latest,GUEST_TOKEN_JWT_SECRET=${SEC_GUEST_JWT}:latest"
