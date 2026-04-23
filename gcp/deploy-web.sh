#!/usr/bin/env bash
# Deploy the Superset web tier (gunicorn, public).
source "$(dirname "$0")/config.sh"

gcloud run deploy bi-superset-web \
  --project "${GCP_PROJECT}" \
  --region "${GCP_REGION}" \
  --image "${SUPERSET_IMAGE}" \
  --service-account "${SA_RUNTIME}" \
  --allow-unauthenticated \
  --cpu 2 \
  --memory 2Gi \
  --concurrency 40 \
  --min-instances 1 \
  --max-instances 4 \
  --port 8088 \
  --timeout 300 \
  --command gunicorn \
  --args='--bind=0.0.0.0:8088,--workers=2,--timeout=120,--worker-class=gthread,--threads=8,superset.app:create_app()' \
  --set-env-vars "SUPERSET_CONFIG_PATH=/app/pythonpath/superset_config.py,WEBDRIVER_BASEURL_USER_FRIENDLY=https://bi.2nth.ai/" \
  --set-secrets "SUPERSET_METADATA_DB_URI=${SEC_METADATA_URI}:latest,REDIS_URL=${SEC_REDIS_URL}:latest,SUPERSET_SECRET_KEY=${SEC_SUPERSET_KEY}:latest,GUEST_TOKEN_JWT_SECRET=${SEC_GUEST_JWT}:latest,MAPBOX_API_KEY=${SEC_MAPBOX}:latest"
