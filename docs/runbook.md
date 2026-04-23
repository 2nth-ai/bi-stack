# bi-stack runbook

Operational playbooks. Keep terse; each section is a recipe.

## Rotating the Superset SECRET_KEY

A new `SECRET_KEY` invalidates all sessions (users get logged out) **and** requires re-encrypting every stored database connection password. Do it during a known-low-traffic window.

```bash
# 1. Generate new key
NEW=$(openssl rand -base64 42)

# 2. Add as a new version in Secret Manager
echo -n "$NEW" | gcloud secrets versions add SUPERSET_SECRET_KEY --data-file=-

# 3. Re-encrypt DB connections (run once against the metadata DB)
gcloud run services update bi-superset-web --region africa-south1 \
  --command superset --args=re-encrypt-secrets
# Confirm success in the logs

# 4. Force new revisions to pick up the secret
for svc in bi-superset-web bi-superset-worker bi-superset-beat; do
  gcloud run services update "$svc" --region africa-south1 \
    --update-labels "secret-rotation=$(date +%Y%m%d)"
done
```

## Rotating the GUEST_TOKEN_JWT_SECRET

**Breaking change** — every currently embedded dashboard stops working on the client side. Coordinate with the biz-demos Worker (same key) before rotating.

```bash
NEW=$(openssl rand -base64 42)
echo -n "$NEW" | gcloud secrets versions add GUEST_TOKEN_JWT_SECRET --data-file=-

# Also update the biz-demos Worker's secret — they must match
wrangler secret put GUEST_TOKEN_JWT_SECRET --name biz-demos-guest-token

# Redeploy Superset web so new tokens sign with the new key
gcloud run services update bi-superset-web --region africa-south1 \
  --update-labels "guest-token-rotation=$(date +%Y%m%d)"
```

Rotation cadence: **annual** unless leak suspected. Calendar it.

## Manual dbt run (backfill or hotfix)

```bash
gcloud run jobs execute bi-dbt-run \
  --region africa-south1 --wait
```

Logs: `gcloud run jobs executions logs <execution-id> --region africa-south1`.

## Promoting a Neon branch

```bash
# From dev → main (e.g. after seed additions)
neon branches restore main --source dev --project-id <project>
# Then re-run dbt against main to rebuild marts
gcloud run jobs execute bi-dbt-run --region africa-south1 --wait
```

## Celery worker health

If dashboards stop refreshing or scheduled reports vanish:

```bash
# Check worker logs
gcloud run services logs read bi-superset-worker --region africa-south1 --limit 100

# Common cause: --no-cpu-throttling got removed by a deploy
gcloud run services describe bi-superset-worker --region africa-south1 \
  --format='value(metadata.annotations.run.googleapis.com/cpu-throttling)'
# Must be "false" — if "true" or missing, redeploy via ./gcp/deploy-worker.sh
```

## Neon connection string change

If Neon rotates an endpoint (rare, but happens on region moves):

```bash
# 1. Update the direct (metadata) secret
echo -n "postgresql+psycopg2://..." | \
  gcloud secrets versions add SUPERSET_METADATA_DB_URI --data-file=-

# 2. Update the pooled (dbt) secret
echo -n "postgresql://..." | \
  gcloud secrets versions add NEON_POOLED_URI --data-file=-

# 3. Redeploy everything
./gcp/deploy-web.sh && ./gcp/deploy-worker.sh && ./gcp/deploy-beat.sh
./gcp/deploy-dbt-job.sh
```

## Disaster recovery

Recreate the whole stack from an empty GCP project:

```bash
export GCP_PROJECT=nth-bi-stack
./gcp/secrets-bootstrap.sh
# Populate each secret from 1Password / Neon dashboard / Upstash dashboard
git tag v0.1.0 && git push --tags  # triggers deploy.yml
```

Dashboards restore from `superset/assets/dashboards/*.zip` via the Superset UI (Settings → Import Dashboards).
