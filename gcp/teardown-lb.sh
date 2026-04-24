#!/usr/bin/env bash
# Tear down the Global HTTPS LB in front of bi-superset-web, reverse order.
# Cloud Run service and Artifact Registry image are left in place.
#
# Usage:
#   export GCP_PROJECT=nth-bi-stack
#   bash gcp/teardown-lb.sh
#
# Idempotent: each delete falls through if the resource is already gone.

source "$(dirname "$0")/config.sh"

NAME_PREFIX="${BI_LB_PREFIX:-bi-superset}"
IP_NAME="${NAME_PREFIX}-ip"
NEG_NAME="${NAME_PREFIX}-neg"
BACKEND_NAME="${NAME_PREFIX}-backend"
URLMAP_NAME="${NAME_PREFIX}-urlmap"
CERT_NAME="${NAME_PREFIX}-cert"
PROXY_NAME="${NAME_PREFIX}-https-proxy"
FWD_NAME="${NAME_PREFIX}-fwd-rule-https"

run() {
  local label=$1; shift
  echo "[teardown] $label"
  "$@" 2>/dev/null || echo "            (already gone)"
}

run "forwarding rule $FWD_NAME" \
  gcloud compute forwarding-rules delete "$FWD_NAME" --global --quiet --project="$GCP_PROJECT"

run "HTTPS proxy $PROXY_NAME" \
  gcloud compute target-https-proxies delete "$PROXY_NAME" --quiet --project="$GCP_PROJECT"

run "SSL cert $CERT_NAME" \
  gcloud compute ssl-certificates delete "$CERT_NAME" --global --quiet --project="$GCP_PROJECT"

run "URL map $URLMAP_NAME" \
  gcloud compute url-maps delete "$URLMAP_NAME" --quiet --project="$GCP_PROJECT"

run "backend service $BACKEND_NAME" \
  gcloud compute backend-services delete "$BACKEND_NAME" --global --quiet --project="$GCP_PROJECT"

run "Serverless NEG $NEG_NAME" \
  gcloud compute network-endpoint-groups delete "$NEG_NAME" --region="$GCP_REGION" --quiet --project="$GCP_PROJECT"

run "global address $IP_NAME" \
  gcloud compute addresses delete "$IP_NAME" --global --quiet --project="$GCP_PROJECT"

echo
echo "LB gone. Remember to remove the DNS A record in your DNS provider too."
