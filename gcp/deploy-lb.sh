#!/usr/bin/env bash
# Provision a Global External HTTPS Load Balancer in front of bi-superset-web.
# Needed because Cloud Run managed domain-mappings aren't supported in
# africa-south1 (returns 501 UNIMPLEMENTED). Seven GCP resources, one DNS
# record, one Google-managed SSL cert.
#
# Usage:
#   export GCP_PROJECT=nth-bi-stack
#   export BI_DOMAIN=bi-superset.2nth.ai     # the public hostname you want
#   bash gcp/deploy-lb.sh
#
# After this runs, the script prints an anycast IP. Add an A record in your
# DNS (Cloudflare: DNS only / grey cloud) pointing that hostname at the IP.
# Managed cert will auto-issue within ~15-45 min once DNS resolves.
#
# Idempotent: every gcloud create falls through with a warning if the
# resource already exists.

source "$(dirname "$0")/config.sh"

: "${BI_DOMAIN:?BI_DOMAIN env var required (e.g. export BI_DOMAIN=bi-superset.2nth.ai)}"
SERVICE="${BI_CR_SERVICE:-bi-superset-web}"

NAME_PREFIX="${BI_LB_PREFIX:-bi-superset}"
IP_NAME="${NAME_PREFIX}-ip"
NEG_NAME="${NAME_PREFIX}-neg"
BACKEND_NAME="${NAME_PREFIX}-backend"
URLMAP_NAME="${NAME_PREFIX}-urlmap"
CERT_NAME="${NAME_PREFIX}-cert"
PROXY_NAME="${NAME_PREFIX}-https-proxy"
FWD_NAME="${NAME_PREFIX}-fwd-rule-https"

echo "[lb] enabling compute.googleapis.com"
gcloud services enable compute.googleapis.com --project="$GCP_PROJECT" >/dev/null

echo "[lb] 1/7 — reserving anycast IP  ($IP_NAME)"
gcloud compute addresses create "$IP_NAME" \
  --network-tier=PREMIUM --ip-version=IPV4 --global --project="$GCP_PROJECT" 2>/dev/null \
  || echo "       already exists"

echo "[lb] 2/7 — Serverless NEG ($NEG_NAME → $SERVICE in $GCP_REGION)"
gcloud compute network-endpoint-groups create "$NEG_NAME" \
  --region="$GCP_REGION" \
  --network-endpoint-type=serverless \
  --cloud-run-service="$SERVICE" \
  --project="$GCP_PROJECT" 2>/dev/null \
  || echo "       already exists"

echo "[lb] 3/7 — backend service ($BACKEND_NAME — no protocol flag)"
gcloud compute backend-services create "$BACKEND_NAME" \
  --global \
  --load-balancing-scheme=EXTERNAL_MANAGED \
  --project="$GCP_PROJECT" 2>/dev/null \
  || echo "       already exists"

echo "[lb]       attaching NEG to backend"
gcloud compute backend-services add-backend "$BACKEND_NAME" \
  --global \
  --network-endpoint-group="$NEG_NAME" \
  --network-endpoint-group-region="$GCP_REGION" \
  --project="$GCP_PROJECT" 2>/dev/null \
  || echo "       already attached"

echo "[lb] 4/7 — URL map ($URLMAP_NAME)"
gcloud compute url-maps create "$URLMAP_NAME" \
  --default-service="$BACKEND_NAME" \
  --project="$GCP_PROJECT" 2>/dev/null \
  || echo "       already exists"

echo "[lb] 5/7 — managed SSL cert ($CERT_NAME for $BI_DOMAIN)"
gcloud compute ssl-certificates create "$CERT_NAME" \
  --domains="$BI_DOMAIN" --global --project="$GCP_PROJECT" 2>/dev/null \
  || echo "       already exists"

echo "[lb] 6/7 — HTTPS target proxy ($PROXY_NAME)"
gcloud compute target-https-proxies create "$PROXY_NAME" \
  --url-map="$URLMAP_NAME" \
  --ssl-certificates="$CERT_NAME" \
  --project="$GCP_PROJECT" 2>/dev/null \
  || echo "       already exists"

echo "[lb] 7/7 — forwarding rule ($FWD_NAME, :443)"
gcloud compute forwarding-rules create "$FWD_NAME" \
  --load-balancing-scheme=EXTERNAL_MANAGED \
  --network-tier=PREMIUM \
  --address="$IP_NAME" \
  --global \
  --target-https-proxy="$PROXY_NAME" \
  --ports=443 \
  --project="$GCP_PROJECT" 2>/dev/null \
  || echo "       already exists"

IP=$(gcloud compute addresses describe "$IP_NAME" --global --project="$GCP_PROJECT" --format='value(address)')

echo
echo "──────────────────────────────────────────────────────────────"
echo "  LB provisioned. Anycast IP: $IP"
echo
echo "  Add DNS A record in your DNS provider:"
echo "     ${BI_DOMAIN}  →  $IP      (Cloudflare: DNS-only / grey cloud)"
echo
echo "  SSL cert will auto-issue 15–45 min after DNS resolves."
echo "  Watch status:"
echo "     gcloud compute ssl-certificates describe $CERT_NAME --global \\"
echo "       --project=$GCP_PROJECT --format='value(managed.status)'"
echo "──────────────────────────────────────────────────────────────"
