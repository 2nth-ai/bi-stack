#!/usr/bin/env bash
# One-time bootstrap: APIs, Artifact Registry, service accounts, Secret Manager,
# Workload Identity Federation for GitHub Actions.
#
# Idempotent — safe to re-run. Requires gcloud auth + GCP_PROJECT env var.
#
# After this runs, populate secrets:
#   echo -n "postgresql+psycopg2://..." | gcloud secrets versions add SUPERSET_METADATA_DB_URI --data-file=-
#   (etc. for each secret)

source "$(dirname "$0")/config.sh"

echo "[bootstrap] enabling APIs"
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  cloudscheduler.googleapis.com \
  iamcredentials.googleapis.com \
  cloudbuild.googleapis.com \
  --project "${GCP_PROJECT}"

echo "[bootstrap] creating Artifact Registry repo ${AR_REPO} in ${GCP_REGION}"
gcloud artifacts repositories create "${AR_REPO}" \
  --repository-format=docker \
  --location="${GCP_REGION}" \
  --description="bi-stack Superset + dbt images" \
  --project "${GCP_PROJECT}" 2>/dev/null || echo "  already exists"

echo "[bootstrap] creating service accounts"
gcloud iam service-accounts create bi-stack-runtime \
  --display-name="bi-stack Cloud Run runtime SA" \
  --project "${GCP_PROJECT}" 2>/dev/null || echo "  runtime SA exists"

gcloud iam service-accounts create bi-stack-deployer \
  --display-name="bi-stack GitHub Actions deployer SA" \
  --project "${GCP_PROJECT}" 2>/dev/null || echo "  deployer SA exists"

echo "[bootstrap] seeding empty secrets (fill in values after)"
for s in "${SEC_METADATA_URI}" "${SEC_ANALYTICS_URI}" "${SEC_NEON_POOLED}" \
         "${SEC_REDIS_URL}" "${SEC_SUPERSET_KEY}" "${SEC_GUEST_JWT}" \
         "${SEC_ADMIN_PW}" "${SEC_MAPBOX}"; do
  gcloud secrets create "$s" --replication-policy=automatic \
    --project "${GCP_PROJECT}" 2>/dev/null || echo "  secret $s exists"
done

echo "[bootstrap] granting runtime SA access to secrets"
for s in "${SEC_METADATA_URI}" "${SEC_ANALYTICS_URI}" "${SEC_NEON_POOLED}" \
         "${SEC_REDIS_URL}" "${SEC_SUPERSET_KEY}" "${SEC_GUEST_JWT}" \
         "${SEC_ADMIN_PW}" "${SEC_MAPBOX}"; do
  gcloud secrets add-iam-policy-binding "$s" \
    --member="serviceAccount:${SA_RUNTIME}" \
    --role=roles/secretmanager.secretAccessor \
    --project "${GCP_PROJECT}" >/dev/null
done

echo "[bootstrap] granting deployer SA roles"
for role in roles/run.admin roles/artifactregistry.writer \
            roles/iam.serviceAccountUser roles/cloudscheduler.admin; do
  gcloud projects add-iam-policy-binding "${GCP_PROJECT}" \
    --member="serviceAccount:${SA_DEPLOYER}" \
    --role="$role" >/dev/null
done

echo "[bootstrap] setting up Workload Identity Federation for GitHub"
POOL="bi-stack-gh"
PROVIDER="github"
GH_REPO="2nth-ai/bi-stack"

gcloud iam workload-identity-pools create "${POOL}" \
  --location=global --display-name="bi-stack GitHub pool" \
  --project "${GCP_PROJECT}" 2>/dev/null || echo "  pool exists"

gcloud iam workload-identity-pools providers create-oidc "${PROVIDER}" \
  --location=global \
  --workload-identity-pool="${POOL}" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository=='${GH_REPO}'" \
  --project "${GCP_PROJECT}" 2>/dev/null || echo "  provider exists"

PROJECT_NUMBER=$(gcloud projects describe "${GCP_PROJECT}" --format='value(projectNumber)')
gcloud iam service-accounts add-iam-policy-binding "${SA_DEPLOYER}" \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL}/attribute.repository/${GH_REPO}" \
  --project "${GCP_PROJECT}" >/dev/null

echo "[bootstrap] done. Workload Identity Provider:"
echo "  projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL}/providers/${PROVIDER}"
echo "  (add this + ${SA_DEPLOYER} as GitHub Actions repository variables WIF_PROVIDER and WIF_SA)"
